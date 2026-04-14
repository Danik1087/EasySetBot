# main.py

import os
import json
import time
import speedtest
import zipfile
from dotenv import load_dotenv
from random import randint
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from libraries.addlibraries import *
from libraries.work_for_ssh import *
from libraries.keyboardtg import *




# Загрузка данных пользователей
def load_users():
    with open('users.json', 'r') as file:
        return json.load(file)


def get_user_role(user_id):
    '''Определяет роль пользователя по его ID'''
    user_id_str = str(user_id)
    # Проверка superadmin
    for superadmin in users_data['superadmin']:
        if superadmin['id'] == user_id_str:
            return 'superadmin'

    # Проверка admins
    for admin in users_data['admins']:
        if admin['id'] == user_id_str:
            return 'admin'

    # Проверка users
    for user in users_data['users']:
        if user['id'] == user_id_str:
            return 'user'

    return None

def check_password(user_id, password):
    '''пароль для администраторов'''
    role = get_user_role(user_id)
    user_id_str = str(user_id)

    if role == 'superadmin':
        for superadmin in users_data['superadmin']:
            if superadmin['id'] == user_id_str:
                return superadmin['password'] == password

    elif role == 'admin':
        for admin in users_data['admins']:
            if admin['id'] == user_id_str:
                return admin['password'] == password

    return False

def is_session_valid(user_id):
    '''действительна ли сессия (15 минут)'''
    if user_id in sessions:
        return (time.time() - sessions[user_id]) < 900
    return False

def has_admin_permission(user_id):
    '''есть ли у пользователя права администратора (с учетом сессии)'''
    role = get_user_role(user_id)
    if role in ['superadmin', 'admin']:
        return is_session_valid(user_id)
    return False

def can_view_only(user_id):
    '''может ли пользователь только просматривать'''
    role = get_user_role(user_id)
    if role == 'user':
        return True
    else:
        return False

def ignore_user(user_id):
    '''нужно ли игнорировать пользователя'''
    return get_user_role(user_id) is None

users_data = load_users()

try:
    load_dotenv('/home/ESBot/EasySetBot/.env')
    TOKEN = os.getenv('TOKEN')
    if TOKEN == None:
        load_dotenv()
        TOKEN = os.getenv('TOKEN')
except Exception as e:
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    print(e)

if users_data['superadmin'][0]['password'] == 'None':
    # Замена данных superadmin
    users_data['superadmin'] = [{'id': os.getenv('ADMIN'), 'password': os.getenv('PASSWORDADM')}]

    # Записывание обратно в файл
    with open('users.json', 'w', encoding='utf-8') as file:
        json.dump(users_data, file, indent=2, ensure_ascii=False)

    users_data = load_users()


application = Application.builder().token(TOKEN).build()
password_error_count = 0


# Словарь для хранения сессий
sessions = {}


# ========================= РАБОТА С САЙТАМИ =========================

async def handle_web_server_selection(query, context, server_type):
    '''Обрабатывает выбор веб-сервера'''
    try:
        if server_type == 'Apache':
            result = shl("cd /etc/apache2/sites-available && ls *.conf 2>/dev/null || echo ''")
        else:  # Nginx
            result = shl("cd /etc/nginx/sites-available && ls 2>/dev/null || echo ''")

        sites = [s.strip() for s in result.stdout.split('\n') if s.strip()]

        # Проверка статуса базового сайта
        default_status = check_default_site_status(server_type)
        default_status_text = '🔴 Включен' if default_status > 0 else '🟢 Отключен'

        if sites:
            message = f'Выберите сайт для {server_type}:\n\n'
            message += f'Статус дефолтного сайта: {default_status_text}'

            await query.edit_message_text(
                message,
                reply_markup=generate_site_list(server_type, sites)
            )

        else:
            context.user_data['step'] = 'name'
            context.user_data['action'] = 'givewebname'
            context.user_data['server'] = server_type
            message = (f'Нет настроенных сайтов. Введите имя нового сайта для {server_type}:\n\n'
            f'Статус дефолтного сайта: {default_status_text}\n⚠️ При создании нового сайта дефолтный будет отключен автоматически.'
            )
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data='website')]])
            )
    except Exception as e:
        print(f'Ошибка при получении списка сайтов: {e}')
        context.user_data['step'] = 'name'
        context.user_data['action'] = 'givewebname'
        context.user_data['server'] = server_type
        await query.edit_message_text(
            f'Введите имя сайта для {server_type}:',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data='website')]])
        )

async def require_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Запрашивает пароль у администратора'''
    user_id = update.effective_user.id
    if ignore_user(user_id):
        return False

    role = get_user_role(user_id)
    if role in ['superadmin', 'admin'] and not is_session_valid(user_id):
        await update.message.reply_text('🔐 Введите пароль для доступа:')
        context.user_data['awaiting_password'] = True

        return True
    return False

# ========================= ПРОВЕРКА ДОСТУПА =========================

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_only=False):
    '''Проверяет доступ пользователя к команде'''
    user_id = update.effective_user.id

    # Игнорирование пользователей не из списка
    if ignore_user(user_id):
        return False

    # Для команд требующих админ прав
    if admin_only:
        if not has_admin_permission(user_id):
            # Проверка, является ли update callback query
            if update.callback_query:
                await update.callback_query.message.reply_text('⚠️ Ваша сессия истекла. Введите пароль заново.')
                context.user_data['awaiting_password'] = True

            else:
                await update.message.reply_text('⚠️ Ваша сессия истекла. Введите пароль заново.')
                context.user_data['awaiting_password'] = True

            return False

    return True

# ========================= МЕНЮ /start =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Игнорирование пользователей не из списка
    if ignore_user(user.id):
        return

    # Определение роли и вызов соответствующего меню
    role = get_user_role(user.id)

    if role == 'user':
        await update.message.reply_text(
            f'📱 Центр управления (пользовательский режим)',
            reply_markup=generate_menu_keyboard(user_mode=True)
        )
    else: # admin или superadmin
        await update.message.reply_text(
            f'📱 Центр управления (административный режим)',
            reply_markup=generate_menu_keyboard(user_mode=False)
        )

    # Проверка была ли выполнена настройка безопасности
    if int(get_config('Port')) == 22:
        await context.bot.send_message(
            chat_id=os.getenv('ADMIN'),
            text='⚠️ Необходима настройка безопасности сервера.',
            reply_markup=generate_menu_security(
                get_config('Port'),
                get_config('PermitRootLogin'),
                get_config('PasswordAuthentication')
            )
        )
# =====================================================================
# ========================= РАБОТА С КНОПКАМИ =========================
# =====================================================================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Игнорирование пользователей не из списка
    if ignore_user(user_id):
        return

    # Разрешенные доступы для пользователей
    user_actions = [
        'gotostart', 'serverinfo', 'characteristics', 'speedtest', 'traffic_consumption'
    ]

    is_admin_action = not query.data in user_actions

    if is_admin_action and not await check_access(update, context, admin_only=True):
        return

    # Очистка критичных состояний при переходе между меню
    if query.data not in ['btn_changesshport', 'btn_changeuserpasswd', 'btn_sshkey', 'console']:
        context.user_data.clear()

    # ========================= СТАРТОВОЕ МЕНЮ =========================

    if query.data == 'gotostart':
        role = get_user_role(user_id)
        if role == 'user':
            await query.edit_message_text(
                text=f'📱 Центр управления (пользовательский режим)',
                reply_markup=generate_menu_keyboard(user_mode=True)
            )
        else:
            await query.edit_message_text(
                text=f'📱 Центр управления (административный режим)',
                reply_markup=generate_menu_keyboard(user_mode=False)
            )

    # ========================== ИНФОРМАЦИЯ О СЕРВЕРЕ ==========================

    elif query.data == 'serverinfo':
        await query.edit_message_text(
            f'ℹ️ Информация о системе',
            reply_markup=generate_menu_serverinfo()
        )

    elif query.data == 'characteristics':
        await query.edit_message_text('Секунду...')
        await query.edit_message_text(serverload(), reply_markup=back1())

    elif query.data == 'speedtest':
        await query.edit_message_text('Секунду...')
        try:
            print('Запуск Speedtest')
            try:
                st = speedtest.Speedtest()
            except Exception as e:
                if e == TimeoutError:
                    await query.edit_message_text('❌ Ошибка time out!')

            await query.edit_message_text('⏳ Выбираем оптимальный сервер...')

            try:
                st.get_best_server()
                print(st.results.server['name'])
            except Exception as e:
                await query.edit_message_text('❌ Сервера speedtest заняты. Подождите пару минут.')
                print(e)

            await query.edit_message_text('📥 Замеряем скорость скачивания...')
            download_speed = st.download() / 1000000
            print(download_speed)

            await query.edit_message_text('📤 Замеряем скорость загрузки...')
            upload_speed = st.upload() / 1000000
            print(upload_speed)

            ping = st.results.ping

            result = (
                '🚀 Результаты теста скорости:\n\n'
                f'▫️ Пинг: {ping:.2f} мс\n'
                f'▫️ Скачивание: {download_speed:.2f} Мбит/с\n'
                f'▫️ Отправка: {upload_speed:.2f} Мбит/с\n\n'
                f"🌍 Сервер: {st.results.server['name']} ({st.results.server['country']})"
            )

            await query.edit_message_text(result,reply_markup=back1())

        except Exception as e:
            await query.edit_message_text('❌ Ошибка при выполнении теста скорости. Подробности в логах сервера.')
            print(e)

    elif query.data == 'traffic_consumption':
        await query.edit_message_text('Секунду...')
        msg = chkvnstat()
        await query.edit_message_text(msg,reply_markup=back1())


    # ========================== ЗАГРУЗКА ==========================


    elif query.data == 'download':
        await query.edit_message_text(
            f'⚙️ Установка и настройка сервисов',
            reply_markup=generate_menu_download()
        )

    elif query.data == 'website':
        await query.edit_message_text(
            f'⚙️ Выберите веб-сервер:',
            reply_markup=generate_menu_webserver()
        )

    elif query.data == 'Apache':
        await handle_web_server_selection(query, context, 'Apache')

    elif query.data == 'Nginx':
        await handle_web_server_selection(query, context, 'Nginx')

    elif query.data.startswith('manage_'):
        # Обработка выбора сайта для управления

        parts = query.data.split('_')
        if len(parts) >= 3:
            server_type = parts[1]
            site_name = '_'.join(parts[2:])

            # Сохранение информации о выбранном сайте
            context.user_data['current_site'] = {
                'name': site_name,
                'server': server_type
            }

            # Получение статуса сервера
            status = get_website_status(server_type)

            await query.edit_message_text(
                f'Управление сайтом: {site_name} ({server_type})',
                reply_markup=generate_site_menu(site_name, server_type, status)
            )

    elif query.data.startswith('create_'):
        # Создание нового сайта
        server_type = query.data.replace('create_', '')

        context.user_data['step'] = 'name'
        context.user_data['action'] = 'givewebname'
        context.user_data['server'] = server_type

        await query.edit_message_text(
            f'Введите имя сайта для {server_type}:',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data=server_type)]])
        )

    elif query.data.startswith('makehttps_'): # Демо
        server_type = query.data.replace('makehttps_', '')
        context.user_data['servertype'] = server_type

        await query.edit_message_text(
            f'Введите ваш домен:',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data=f'back_to_{server_type}_list')]])
        )


    elif query.data.startswith('start_'):
        server_type = query.data.replace('start_', '')
        current_site = context.user_data.get('current_site', {})

        start_web_server(server_type)
        status = get_website_status(server_type)

        await query.edit_message_text(
            f'Сервер {server_type} запущен.\nТекущий статус: {status}',
            reply_markup=generate_site_menu(current_site.get('name', ''), server_type, status)
        )

    elif query.data.startswith('stop_'):
        server_type = query.data.replace('stop_', '')
        site = context.user_data.get('current_site', {})

        stop_web_server(server_type)
        status = get_website_status(server_type)

        await query.edit_message_text(
            f'Сервер {server_type} остановлен.\nТекущий статус: {status}',
            reply_markup=generate_site_menu(site.get('name', ''), server_type, status)
        )

    elif query.data.startswith('upload_'):
        # Запрос на загрузку файлов

        parts = query.data.split('_')
        if len(parts) >= 3:
            server_type = parts[1]
            site_name = '_'.join(parts[2:])

            context.user_data['awaiting_archive_site'] = True
            context.user_data['upload_site'] = {
                'name': site_name,
                'server': server_type
            }

            await query.edit_message_text(
                f'Загрузите ZIP-архив с файлами для сайта {site_name}.\n\n'
                f'Архив будет распакован в /var/www/{site_name}/',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Отмена', callback_data=f'manage_{server_type}_{site_name}')]])
            )

    elif query.data.startswith('back_to_'):
        # Обработка кнопки Назад из меню управления сайтом
        parts = query.data.split('_')
        if len(parts) >= 4:
            server_type = parts[2]  # Apache или Nginx

            await handle_web_server_selection(query, context, server_type)

    elif query.data.startswith('delete_'):
        # Подтверждение удаления сайта
        parts = query.data.split('_')

        if len(parts) >= 3:
            server_type = parts[1]
            site_name = '_'.join(parts[2:])

            # Сохранение информации для подтверждения
            context.user_data['pending_deletion'] = {
                'server': server_type,
                'name': site_name
            }

            await query.edit_message_text(
                f"⚠️ Вы уверены, что хотите удалить сайт '{site_name}'?\n\n"
                f'Будет удалено:\n'
                f'• Конфигурация сайта\n'
                f'• Все файлы в /var/www/{site_name}/\n'
                f'• Настройки веб-сервера\n\n'
                f'Это действие необратимо!\n\n'
                f'Для подтверждения введите "ДА, УДАЛИТЬ {site_name}" (без кавычек):',

                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('❌ Отмена', callback_data=f'manage_{server_type}_{site_name}')]
                ])
            )

    elif query.data == 'site_status':
        current_site = context.user_data.get('current_site', {})
        if current_site:
            status = get_website_status(current_site['server'])
            default_status = check_default_site_status(current_site['server'])

            message = (
                f'📊 Статус сайта {current_site["name"]}:\n\n'
                f'• Веб-сервер: {current_site["server"]}\n'
                f'• Статус: {"🟢 Активен" if status == "active" else "🔴 Неактивен"}\n'
                f'• Дефолтный сайт: {"🔴 Включен" if default_status > 0 else "🟢 Отключен"}\n\n'
                f'Директория файлов: /var/www/{current_site["name"]}/'
            )

            await query.edit_message_text(
                message,
                reply_markup=generate_site_menu(current_site['name'], current_site['server'], status)
            )


# ========================== ДОПОЛНИТЕЛЬНО ==========================


    elif query.data == 'additionally':
        await query.edit_message_text(
            f'⚒️ Инструменты и настройки',
            reply_markup=generate_menu_additionally()
        )

    elif query.data == 'console': # Консоль
        context.user_data['action'] = 'givecommand'
        context.user_data['console'] = '===============CONSOLE===============\n\nИнтерактивная оболочка не поддерживается.\nИстория команд не сохраняется.\n\n~$ '
        context.user_data['query'] = query
        await query.edit_message_text(
                context.user_data.get('console'),
                reply_markup=back3()
            )
    elif query.data == 'editfile': # Работа с файлами
        await query.edit_message_text(
                f'Меню работы с файлами.',
                reply_markup=generate_menu_files()
                )

    elif query.data.startswith('workfiles_'): # Изменение файлов
        part = query.data.split('_')[1]

        if part == 'loadfiles':
            context.user_data['action'] = 'location_load'
            await query.edit_message_text(
                f'Укажите расположение куда будет распакован zip архив:',
                reply_markup=back3()
            )

        elif part == 'uploadfiles':
            context.user_data['action'] = 'location_upload'
            await query.edit_message_text(
                f'Укажите полный путь к файлу, который нужно скачать (например: /home/user/file.txt):',
                reply_markup=back3()
            )

        elif part == 'loadscript':
            context.user_data['awaiting_script'] = True
            await query.edit_message_text(
                f'Отправьте скрипт формата .sh',
                reply_markup=back3()
            )

    elif query.data == 'managesecurity':
        await query.edit_message_text(
            f'🔒 Настройка безопасности',
            reply_markup=generate_menu_security(get_config('Port'), get_config('PermitRootLogin'), get_config('PasswordAuthentication'))
        )

    elif query.data == 'btn_autosecurity':
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выполняется настройка безопасности...'
        )
        changesshport(randint(1025, 65535))
        downloadUFW()
        rootnologin(0)
        passwdnologin(0)
        downlfail2ban()
        updatesystem()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Настройка безопасности выполнена.\nПерезагрузка.'
        )
        shl('reboot')


    elif query.data == 'btn_changesshport':
        context.user_data['action'] = 'changesshport'
        await query.edit_message_text(
                f'Введите порт... (число в промежутке 1024 и 65535 невключительно)',
                reply_markup=backsecurity()
            )

    elif query.data == 'btn_downloadUFW':
        downloadUFW()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='UFW успешно установлен.'
        )

    elif query.data == 'btn_changeuserpasswd':
        context.user_data['action'] = 'changeuserpasswd'
        context.user_data['step'] = 'username'
        await query.edit_message_text(
                f'Введите имя пользователя... ',
                reply_markup=backsecurity()
            )

    elif query.data == 'btn_sshkey':
        context.user_data['action'] = 'sshkey'
        context.user_data['step'] = 'username'
        await query.edit_message_text(
                f'Введите имя пользователя... ',
                reply_markup=backsecurity()
            )

    elif query.data == 'btn_rootnologin':
        if get_config('PermitRootLogin') == 'yes':
            rootnologin(0)

        else:
            rootnologin(1)



        await query.edit_message_text(
                f'🔒 Настройка безопасности',
                reply_markup=generate_menu_security(get_config('Port'), get_config('PermitRootLogin'), get_config('PasswordAuthentication'))
            )

    elif query.data == 'btn_passwdnologin':
        if get_config('PasswordAuthentication') == 'yes':
            passwdnologin(y=0)

        else:
            passwdnologin(y=1)

        await query.edit_message_text(
                f'🔒 Настройка безопасности',
                reply_markup=generate_menu_security(get_config('Port'), get_config('PermitRootLogin'), get_config('PasswordAuthentication'))
            )

    elif query.data == 'btn_downlfail2ban':
        downlfail2ban()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='fail2ban успешно установлен.'
        )

    elif query.data == 'updatesystem':
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Обновление системы может занять некоторое время.'
        )
        updatesystem()
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Система успешно обновлена.'
        )

    elif query.data == 'reboot':
        print('Перезагрузка машины...')
        await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Перезагрузка машины... \nБот будет не доступен в течении некоторого времени.'
        )
        shl('reboot')



    elif query.data == 'gotoadditionally':
        await query.edit_message_text(
                f'🔒 Настройка безопасности',
                reply_markup=generate_menu_security(get_config('Port'), get_config('PermitRootLogin'), get_config('PasswordAuthentication'))
            )

# ====================================================================
# ========================= РАБОТА С ТЕКСТОМ =========================
# ====================================================================

async def texthandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Игнорирование пользователей не из списка
    user_id = update.effective_user.id
    if ignore_user(user_id):
        return



    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    global password_error_count
    text = update.message.text


    # Проверка доступа для обычных пользователей
    if can_view_only(user_id):
        await update.message.reply_text('⛔ У вас есть права только на просмотр информации.')
        return

    # ========================= Проверка пароля =========================

    if context.user_data.get('awaiting_password'):
        role = get_user_role(user_id)
        if role in ['superadmin', 'admin']:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)

            if check_password(user_id, text):
                sessions[user_id] = time.time()
                context.user_data['awaiting_password'] = False
                await update.message.reply_text(
                    '✅ Пароль принят. Сессия активна 15 минут.',
                    reply_markup=generate_menu_keyboard(False)
                )
                password_error_count = 0

            else:
                await update.message.reply_text('❌ Неверный пароль. Попробуйте еще раз:')
                password_error_count += 1

                if password_error_count >= 10:
                    print('Исчерпаны попытки ввода пароля.')
                    print('Завершение работы...')
                    shl('systemctl stop esbot')
                    exit(1)

        return

    # Проверка доступа для администраторов
    if not await check_access(update, context, admin_only=True):
        return

    # Получение выбранного действия пользователем
    action = context.user_data.get('action')

    # ========================= Работа с сайтом =========================
    if context.user_data.get('pending_deletion'):
        pending = context.user_data['pending_deletion']
        confirmation_text = f"ДА, УДАЛИТЬ {pending['name']}"

        if text == confirmation_text:
            # Удаление сайта
            success, message = delete_site(pending['server'], pending['name'])

            if success:
                await update.message.reply_text(
                    f'✅ {message}',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data=pending['server'])]])
                )
            else:
                await update.message.reply_text(
                    f'❌ {message}',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data=f"manage_{pending['server']}_{pending['name']}")]])
                )

            # Очистка состояния
            context.user_data.pop('pending_deletion', None)
        else:
            await update.message.reply_text(
                f'❌ Подтверждение не совпадает. Удаление отменено.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data=f"manage_{pending['server']}_{pending['name']}")]])
            )
            context.user_data.pop('pending_deletion', None)
        return

    elif action == 'givewebname':
        step = context.user_data.get('step')
        if step == 'name':
            print(f'Имя: {text}')
            context.user_data['webname'] = text
            context.user_data['step'] = 'giveconfig'
            await update.message.reply_text(
                f'Введите конфигурацию для вашего сервера {text}:',
                reply_markup=backsecurity()
            )

        elif step == 'giveconfig':
            config = text
            webname = context.user_data.get('webname')
            print(config)
            if webname != None and config != None:
                server = context.user_data.get('server')
                if server == 'Apache':
                    success, message = installApache(webname, config)
                    if success:
                        await update.message.reply_text(
                            f'✅ {message}\n\nДефолтный сайт отключен.',
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data='website')]])
                        )
                    else:
                        await update.message.reply_text(
                            f'❌ {message}',
                            reply_markup=backsecurity()
                        )
                elif server == 'Nginx':
                    success, message = installNginx(webname, config)
                    if success:
                        await update.message.reply_text(
                            f'✅ {message}\n\nДефолтный сайт отключен.',
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Назад', callback_data='website')]])
                        )
                    else:
                        await update.message.reply_text(
                            f'❌ {message}',
                            reply_markup=backsecurity()
                        )
                context.user_data.clear()

    elif action == 'givedomain': # Получение домена
        domain = text
        server_type = context.user_data.get('servertype')
        certbot_setup(server_type, domain)
        await update.message.reply_text(
                f'Https настроен!',
                reply_markup=[InlineKeyboardButton('Назад', callback_data=f'back_to_{server_type}_list')]
            )

    # ========================= Консоль =========================
    elif action == 'givecommand': # Консоль
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        result = shl(text)
        output = str(result.stdout)
        print(output)
        if result.returncode != 0:
            output = result.stderr

        console = str(context.user_data.get('console')) + str(text) + '\n' + str(output) + '\n' + '~$ '
        context.user_data['console'] = console
        query = context.user_data.get('query')
        await query.edit_message_text(
                    console,
                    reply_markup=back3()

                )

    # ========================= Работа с файлами =========================

    elif action.startswith('location_'):
        part = action.split('_')[1]

        if part == 'load':
            # Проверка существования директории
            if os.path.isdir(text):
                context.user_data['location'] = text
                context.user_data['awaiting_archive'] = True
                await update.message.reply_text(
                    f'✅ Директория найдена: {text}\nОтправьте ZIP-архив для распаковки:',
                    reply_markup=back3()
                )
            else:
                await update.message.reply_text(
                    f'❌ Директория не найдена! Проверьте путь.',
                    reply_markup=back3()
                )

        elif part == 'upload':
            # Проверка существования файла
            if os.path.isfile(text):
                try:
                    # Отправка файла пользователю
                    with open(text, 'rb') as file:
                        await update.message.reply_document(
                            document=file,
                            caption=f'📁 Файл: {os.path.basename(text)}'
                        )
                    await update.message.reply_text(
                        '✅ Файл отправлен!',
                        reply_markup=back3()
                    )
                except Exception as e:
                    await update.message.reply_text(
                        f'❌ Ошибка при отправке файла: {str(e)}',
                        reply_markup=back3()
                    )
                finally:
                    context.user_data.clear()
            else:
                await update.message.reply_text(
                    f'❌ Файл не найден! Проверьте путь.',
                    reply_markup=back3()
                )

    # ========================= Работа с конфигом ssh =========================

    if action == 'changesshport': # ssh порт
        try:
            port = int(text)
            if 1024 < port <= 65535:
                changesshport(port)
                await update.message.reply_text(
                    f'Порт SSH изменен на {port}.',
                    reply_markup=backsecurity()
                )
                context.user_data.clear()
            else:
                await update.message.reply_text(
                    f'Порт должен быть в диапазоне от 1025 до 65535.',
                    reply_markup=backsecurity()
                )
        except ValueError:
            await update.message.reply_text(
                f'Порт должен быть числом.',
                reply_markup=backsecurity()
            )

    elif action == 'changeuserpasswd':
        step = context.user_data.get('step')

        if step == 'username':
            context.user_data['username'] = text
            context.user_data['step'] = 'password'
            await update.message.reply_text(
                f'Введите новый пароль для пользователя {text}:',
                reply_markup=backsecurity()
            )
        elif step == 'password':
            username = context.user_data.get('username')
            password = text
            changeuserpasswd(username, password)
            await update.message.reply_text(
                f'Пароль для пользователя {username} изменен.',
                reply_markup=backsecurity()
            )
            context.user_data.clear()

    elif action == 'sshkey':
        step = context.user_data.get('step')

        if step == 'username':
            username = text
            sshkey(username)
            await update.message.reply_text(
                f'SSH ключ для пользователя {username} создан. Крайне рекомендую удалить его из чата после сохранения.',
                reply_markup=backsecurity()

            )
            with open(f'/home/{username}/.ssh/id_ed25519', 'rb') as file:
                await update.message.reply_document(document=file)
            context.user_data.clear()

    if context.user_data.get('awaiting_archive_site'):
        await update.message.reply_text('Пожалуйста, загрузите ZIP-архив как документ.')
        return




async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''Обрабатывает загруженные документы (архивы, файлы)'''
    user_id = update.effective_user.id
    if ignore_user(user_id):
        return

    if not await check_access(update, context, admin_only=True):
        return

    # ========================= Получение архива сайта =========================

    if context.user_data.get('awaiting_archive_site'):
        document = update.message.document
        file_name = document.file_name

        # Проверка, что это ZIP файл
        if not file_name.endswith('.zip'):
            await update.message.reply_text('Пожалуйста, загрузите файл в формате ZIP.')
            return

        # Скачивание файла
        file = await context.bot.get_file(document.file_id)
        temp_path = f'/tmp/{file_name}'
        await file.download_to_drive(temp_path)

        # Получение информации о сайте
        site_info = context.user_data.get('upload_site')
        if not site_info:
            await update.message.reply_text('Ошибка: информация о сайте не найдена.')
            return

        # Распаковка архива
        success, message = extract_archive_to_site(temp_path, site_info['name'])

        # Удаление временного файла
        try:
            os.remove(temp_path)
        except:
            pass

        if success:
            await update.message.reply_text(
                f'✅ {message}\n\n'
                f'Файлы успешно загружены в директорию сайта.',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться к управлению', 
                    callback_data=f"manage_{site_info['server']}_{site_info['name']}")]])
            )
        else:
            await update.message.reply_text(
                f'❌ {message}',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Вернуться к управлению', 
                    callback_data=f"manage_{site_info['server']}_{site_info['name']}")]])
            )

        # Очистка состояния
        context.user_data.pop('awaiting_archive_site', None)
        context.user_data.pop('upload_site', None)

    # ========================= Вставка архива =========================

    elif context.user_data.get('awaiting_archive'):
        document = update.message.document
        file_name = document.file_name

        # Проверка, что это ZIP архив
        if not file_name or not file_name.endswith('.zip'):
            await update.message.reply_text(
                '❌ Пожалуйста, загрузите файл в формате ZIP.',
                reply_markup=back3()
            )
            return

        # Скачивание файла
        file = await context.bot.get_file(document.file_id)
        temp_path = f'/tmp/{file_name}'

        try:
            await file.download_to_drive(temp_path)

            # Получение директории
            target_dir = context.user_data.get('location')
            if not target_dir or not os.path.isdir(target_dir):
                await update.message.reply_text(
                    '❌ Целевая директория не найдена. Начните заново.',
                    reply_markup=back3()
                )
                return

            # Распаковка архива
            try:
                with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)

                await update.message.reply_text(
                    f'✅ Архив успешно распакован в:\n{target_dir}',
                    reply_markup=back3()
                )

            except zipfile.BadZipFile:
                await update.message.reply_text(
                    '❌ Ошибка: файл поврежден или не является ZIP-архивом.',
                    reply_markup=back3()
                )
            except Exception as e:
                await update.message.reply_text(
                    f'❌ Ошибка при распаковке: {str(e)}',
                    reply_markup=back3()
                )

        except Exception as e:
            await update.message.reply_text(
                f'❌ Ошибка при загрузке файла: {str(e)}',
                reply_markup=back3()
            )
        finally:
            # Удаление временного файла
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

            # Очистка состояния
            context.user_data.pop('awaiting_archive', None)
            context.user_data.pop('location', None)

    # ========================= Обработка скриптов .sh =========================

    elif context.user_data.get('awaiting_script'):
        document = update.message.document
        file_name = document.file_name

        if not file_name or not file_name.endswith('.sh'):
            await update.message.reply_text(
                '❌ Пожалуйста, загрузите файл в формате .sh',
                reply_markup=back3()
            )
            return

        file = await context.bot.get_file(document.file_id)
        temp_path = f'/tmp/{file_name}'

        try:
            await file.download_to_drive(temp_path)

            # Выдача права на исполнение
            shl(f'chmod 755 {temp_path}')

            # Запуск скрипта
            result = shl(f'bash {temp_path}')

            # Получение обратной информации
            response = (f'📋 Результат выполнения скрипта:\n\n'
                f'Код возврата: {result.returncode}\n'
            )

            if result.stdout:
                response += f'Вывод:\n{result.stdout[:1500]}\n'
            if result.stderr:
                response += f'Ошибки:\n{result.stderr[:1500]}\n'

            await update.message.reply_text(
                response,
                reply_markup=back3()
            )

        except Exception as e:
            await update.message.reply_text(
                f'❌ Ошибка при обработке скрипта: {str(e)}',
                reply_markup=back3()
            )
        finally:
            # Удаление временного файла
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

            # Очистка состояния
            context.user_data.pop('awaiting_script', None)

# ========================= Добавление обработчиков =========================

application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(menu))
application.add_handler(MessageHandler(filters.TEXT, texthandler))
application.add_handler(MessageHandler(filters.Document.ALL, document_handler))

if __name__ == '__main__':
    print('Запуск EasySetBot')
    application.run_polling()
