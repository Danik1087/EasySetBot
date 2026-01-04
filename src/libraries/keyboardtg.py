# keyboardtg.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def generate_menu_keyboard(user_mode):
    '''Главное меню'''
    print()
    if user_mode == False:
        buttons = [
            [InlineKeyboardButton('Информация', callback_data='serverinfo')],
            [InlineKeyboardButton('Установить', callback_data='download')],
            [InlineKeyboardButton('Дополнительно', callback_data='additionally')]
        ]
    else:
        buttons = [[InlineKeyboardButton('Информация', callback_data='serverinfo')]]
    return InlineKeyboardMarkup(buttons)

def generate_menu_serverinfo():
    '''Меню информации'''
    buttons = [
            [InlineKeyboardButton('Системные характеристики', callback_data='characteristics')],
            [InlineKeyboardButton('Скорость интернета', callback_data='speedtest')],
            [InlineKeyboardButton('Расход трафика', callback_data='traffic_consumption')],
            [InlineKeyboardButton('Назад', callback_data='gotostart')]
        ]
    return InlineKeyboardMarkup(buttons)

def generate_menu_download():
    '''Меню скачивания'''
    buttons = [
            [InlineKeyboardButton('Веб-сайт', callback_data='website')],
            [InlineKeyboardButton('Назад', callback_data='gotostart')]
        ]
    return InlineKeyboardMarkup(buttons)

def generate_menu_additionally():
    '''Меню второстепенных функций'''
    buttons = [
            [InlineKeyboardButton('Настройка безопасности', callback_data='managesecurity')],
            [InlineKeyboardButton('Работа с файлами', callback_data='editfile')],
            [InlineKeyboardButton('Консоль', callback_data='console')],
            [InlineKeyboardButton('Назад', callback_data='gotostart')]
        ]
    return InlineKeyboardMarkup(buttons)

def back1():
    '''Возврат в информацию сервера'''
    buttons = [
            [InlineKeyboardButton('Назад', callback_data='serverinfo')]
        ]
    return InlineKeyboardMarkup(buttons)

def back2():
    '''Возврат в меню скачивания'''
    buttons = [
            [InlineKeyboardButton('Назад', callback_data='gotodownload')]
        ]
    return InlineKeyboardMarkup(buttons)

def back3():
    '''Возврат в меню дополнительно'''
    buttons = [
            [InlineKeyboardButton('Назад', callback_data='additionally')]
        ]
    return InlineKeyboardMarkup(buttons)

def backsecurity():
    '''Возврат в под меню настройка безопасности'''
    buttons = [
            [InlineKeyboardButton('Назад', callback_data='managesecurity')]
        ]
    return InlineKeyboardMarkup(buttons)



def generate_menu_security(portssh, rootaccess, passwdaccess):
    '''Подменю настройка безопасности'''
    buttons = [
            [InlineKeyboardButton( '🤖 Автонастройка', callback_data='btn_autosecurity')],
            [InlineKeyboardButton(f'🔧 SSH порт: {portssh}', callback_data='btn_changesshport')],
            [InlineKeyboardButton( '🛡️ Установить UFW', callback_data='btn_downloadUFW')],
            [InlineKeyboardButton( '🔑 Сменить пароль', callback_data='btn_changeuserpasswd')],
            [InlineKeyboardButton( '🗝️ Создать SSH-ключ', callback_data='btn_sshkey')],
            [InlineKeyboardButton(f'👑 Вход по Root: {rootaccess}', callback_data='btn_rootnologin')],
            [InlineKeyboardButton(f'🗝️ Вход по паролю: {passwdaccess}', callback_data='btn_passwdnologin')],
            [InlineKeyboardButton( '🚫 Установить Fail2Ban', callback_data='btn_downlfail2ban')],
            [InlineKeyboardButton( '🆕 Обновить систему', callback_data='updatesystem')],
            [InlineKeyboardButton( '🔄 Перезагрузка', callback_data='reboot')],
            [InlineKeyboardButton( 'Назад', callback_data='additionally')]
        ]
    return InlineKeyboardMarkup(buttons)


def generate_menu_files():
    '''Подменю работа с файлами'''
    buttons = [
            [InlineKeyboardButton( '📥 Загрузить файл', callback_data='workfiles_loadfiles')],
            [InlineKeyboardButton(f'📤 Выгрузить файл', callback_data='workfiles_uploadfiles')],
            [InlineKeyboardButton( '🔧 Загрузить скрипт', callback_data='workfiles_loadscript')],
        ]
    return InlineKeyboardMarkup(buttons)


def generate_menu_webserver():
    '''Подменю создание веб-сервера'''
    buttons = [
            [InlineKeyboardButton( 'Apache', callback_data='Apache')],
            [InlineKeyboardButton( 'Nginx', callback_data='Nginx')],
            [InlineKeyboardButton( 'Назад', callback_data='download')]
        ]
    return InlineKeyboardMarkup(buttons)


def generate_site_menu(site_name, server_type, status='unknown'):
    '''Подменю управления сайтом'''
    status_icon = '🟢' if status == 'active' else '🔴'
    buttons = [
        [InlineKeyboardButton(f'{status_icon} Статус: {status}', callback_data='site_status')],
        [InlineKeyboardButton('▶️ Запуск', callback_data=f'start_{server_type}')],
        [InlineKeyboardButton('⏹️ Выключение', callback_data=f'stop_{server_type}')],
        [InlineKeyboardButton('📤 Загрузка файлов', callback_data=f'upload_{server_type}_{site_name}')],
        [InlineKeyboardButton('🗑️ Удалить сайт', callback_data=f'delete_{server_type}_{site_name}')],
        [InlineKeyboardButton('Назад', callback_data=f'back_to_{server_type}_list')]
    ]
    return InlineKeyboardMarkup(buttons)


def generate_site_list(server_type, sites):
    '''Список сайтов'''
    buttons = []
    for site in sites:
        # Убираем расширение .conf для Apache
        if server_type == 'Apache':
            site_name = site.replace('.conf', '')
        else:
            site_name = site
        buttons.append([InlineKeyboardButton(site_name, callback_data=f'manage_{server_type}_{site_name}')])

    buttons.append([InlineKeyboardButton('➕ Создать новый сайт', callback_data=f'create_{server_type}')])
    buttons.append([InlineKeyboardButton('➕ Настроить https (демо)', callback_data=f'makehttps_{server_type}')])
    buttons.append([InlineKeyboardButton('Назад', callback_data='website')])  # Возврат к выбору сервера
    return InlineKeyboardMarkup(buttons)
