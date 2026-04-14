# addlibraries.py

import zipfile
import subprocess
import psutil
import shutil
import json
from libraries.keyboardtg import *
from random import randint

def load_users():
    with open('users.json', 'r') as file:
        return json.load(file)

def passwd(a):
        password = str()
        alltext = '1234567890'
        for i in range(a):
            password = password + alltext[randint(0, len(alltext)-1)]
        return password

def shl(cmd):
    '''Отправляет команды в консоль shell=True, capture_output=True, text=True'''
    print(f'Выполнение команды: {cmd}')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'Ошибка команды {cmd}: {result.stderr}')
    return result


# Информация о системе

def progress_bar(percent, bar_length=10):
    '''Создание прогресс бара, принимает процент и размер'''
    filled = '▰' * int(round(percent / 10))
    empty = '▱' * (bar_length - len(filled))
    return f'{filled}{empty}'


def serverload():
    '''Мониторинг загруженности psutil'''
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        print('Запуск мониторинга загруженности')

        text = (
            f'🖥 VPS Мониторинг загруженности\n\n'

            f'🔹 RAM Использование\n'
            f'{progress_bar(memory.percent)} {memory.percent}%\n'
            f'{memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB\n\n'

            f'🔸 CPU Использование\n'
            f'{progress_bar(cpu_percent)} {cpu_percent}%\n'
            f'Ядра: {psutil.cpu_count(logical=True)}\n'
            f'Частота: {psutil.cpu_freq().current} MHz\n\n'

            f'🔹 SSD Использование ({psutil.disk_partitions()[0].device})\n'
            f'{progress_bar(disk.percent)} {disk.percent}%\n'
            f'Использованно: {disk.used / (1024**3):.2f} GB\n'
            f'Свободно: {disk.free / (1024**3):.2f} GB\n'
            f'Всего: {disk.total / (1024**3):.2f} GB\n\n'

            f'🔸 Активные процессы\n'
            f'{len(psutil.pids())} активны'
            )
        return text
    except Exception as e:
        print(e)


def checkstat(data, a='t'): # h d m t
    '''Получение из json трафик интернета'''
    try:
        if not a:
            return 0, 0

        if a == 't':
            rx = data['interfaces'][0]['traffic']['total']['rx']
            tx = data['interfaces'][0]['traffic']['total']['tx']

        elif a == 'h':
            rx = data['interfaces'][0]['traffic']['hour'][-1]['rx']
            tx = data['interfaces'][0]['traffic']['hour'][-1]['tx']

        elif a == 'd':
            rx = data['interfaces'][0]['traffic']['day'][-1]['rx']
            tx = data['interfaces'][0]['traffic']['day'][-1]['tx']

        elif a == 'm':
            rx = data['interfaces'][0]['traffic']['month'][-1]['rx']
            tx = data['interfaces'][0]['traffic']['month'][-1]['tx']


        return rx, tx
    except Exception as e:
        print(e)
        return None, None

def formatstat(data, period):
    '''Форматирует данные трафика в читаемый вид'''
    rx, tx = checkstat(data, period)
    if rx is None or tx is None:
        return 'Ошибка получения данных'

    if rx == 0 and tx == 0:
        return 'Данные отсутствуют'

    result = (
        f'▼ Приём: {rx / (1024**3):.2f} ГБ\n'
        f'▲ Отправка: {tx / (1024**3):.2f} ГБ\n'
        f'▬ Итого: {(rx+tx) / (1024**3):.2f} ГБ\n\n'
    )
    return result

def chkvnstat():
    '''Получает трафик и возвращает готовый отчет'''
    try:
        cmd = ['vnstat', '--json']
        data_str = subprocess.check_output(cmd, timeout=10).decode('utf-8')
        data = json.loads(data_str)

        h = formatstat(data, 'h')
        d = formatstat(data, 'd')
        m = formatstat(data, 'm')
        t = formatstat(data, 't')

        msg = (
            f'📊 Трафик за час\n{h}\n'
            f'📊 Трафик за день\n{d}\n'
            f'📊 Трафик за месяц\n{m}\n'
            f'📊 Трафик за всё время\n{t}\n'
        )
        return msg
    except subprocess.CalledProcessError as e:
        return f'Ошибка выполнения vnstat: {e}'
    except json.JSONDecodeError as e:
        return f'Ошибка парсинга JSON: {e}'
    except Exception as e:
        return f'Неизвестная ошибка: {e}'

def disable_default_site(server_type):
    '''Отключает базовый сайт Apache или Nginx'''
    if server_type == 'Apache':
        # Отключение базовый сайт Apache
        shl('a2dissite 000-default.conf 2>/dev/null || true')
        shl('a2dissite default-ssl.conf 2>/dev/null || true')
        shl('systemctl reload apache2')
    elif server_type == 'Nginx':
        # Удаление указателя базового сайта Nginx
        shl('rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true')
        shl('systemctl reload nginx')

def delete_site(server_type, site_name):
    '''Удаляет сайт'''
    if server_type == 'Apache':
        # Отключение сайта
        shl(f'a2dissite {site_name}.conf 2>/dev/null || true')
        # Удаление конфигурационного файла
        shl(f'rm -f /etc/apache2/sites-available/{site_name}.conf 2>/dev/null || true')
        # Удаление директории с файлами
        shl(f'rm -rf /var/www/{site_name} 2>/dev/null || true')
        # Перезагрузка Apache
        shl('systemctl reload apache2')
        return True, f'Сайт {site_name} удален из Apache'
    elif server_type == 'Nginx':
        # Удаление указателя
        shl(f'rm -f /etc/nginx/sites-enabled/{site_name} 2>/dev/null || true')
        # Удаление конфигурационного файла
        shl(f'rm -f /etc/nginx/sites-available/{site_name} 2>/dev/null || true')
        # Удаление директории с файлами
        shl(f'rm -rf /var/www/{site_name} 2>/dev/null || true')
        # Перезагрузка Nginx
        shl('systemctl reload nginx')
        return True, f'Сайт {site_name} удален из Nginx'
    return False, 'Неизвестный тип сервера'

def check_default_site_status(server_type):
    '''Проверяет статус базового сайта'''
    if server_type == 'Apache':
        result = shl('ls -la /etc/apache2/sites-enabled/ | grep "000-default\|default-ssl" | wc -l')
        return int(result.stdout.strip())
    elif server_type == 'Nginx':
        result = shl('ls -la /etc/nginx/sites-enabled/ | grep "default" | wc -l')
        return int(result.stdout.strip())
    return 0


def installApache(name, config):
    print('Начинаю установку Apache...')
    # Установка Apache
    shl('apt update -y')
    shl('apt install apache2 -y')
    shl('systemctl enable apache2')

    # Отключение базового сайта
    disable_default_site('Apache')

    # Размещение файлов сайта и настройка прав
    shl(f'mkdir -p /var/www/{name}')
    shl(f'chown -R $USER:$USER /var/www/{name}')
    shl('chmod -R 755 /var/www')

    # Настройка конфигурации
    with open(f'/etc/apache2/sites-available/{name}.conf', 'w', encoding='utf-8') as file:
        file.write(config)

    # Активация сайта
    try:
        shl(f'a2ensite {name}.conf')
    except Exception as e:
        return e
    shl('ufw allow 80/tcp') # Открытие портов в ufw
    shl("ufw allow 'Apache'")

    shl('systemctl reload apache2')
    return True, f'Сайт {name} установлен в Apache'

def installNginx(name, config):
    print('Начинаю установку Nginx...')
    # Установка Nginx
    shl('apt update -y')
    shl('apt install nginx -y')
    shl('systemctl enable nginx')

    # Отключение базового сайта
    disable_default_site('Nginx')

    # Размещение файлов сайта и настройка прав
    shl(f'mkdir -p /var/www/{name}')
    shl(f'chown -R $USER:$USER /var/www/{name}')
    shl('chmod -R 755 /var/www')

    # Настройка конфигурации
    with open(f'/etc/nginx/sites-available/{name}', 'w', encoding='utf-8') as file:
        file.write(config)

    # Активация сайта
    shl(f'ln -s /etc/nginx/sites-available/{name} /etc/nginx/sites-enabled/')
    try:
        shl(f'nginx -t')
    except Exception as e:
        return False, f'Ошибка конфигурации: {e}'
    shl("ufw allow 'Nginx HTTP'")

    shl('systemctl reload nginx')
    return True, f'Сайт {name} установлен в Nginx'


def get_website_status(server_type):
    '''Проверяет статус сайта'''
    if server_type == 'Apache':
        result = shl(f'systemctl is-active apache2')
        if result.stdout.strip() == 'active':
            return 'active'
        else:
            return 'inactive'

    elif server_type == 'Nginx':
        result = shl(f'systemctl is-active nginx')
        if result.stdout.strip() == 'active':
            return 'active'
        else:
            return 'inactive'
    return 'unknown'

def start_web_server(server_type):
    '''Запускает веб-сервер'''
    if server_type == 'Apache':
        shl('systemctl start apache2')
    elif server_type == 'Nginx':
        shl('systemctl start nginx')

def stop_web_server(server_type):
    '''Останавливает веб-сервер'''
    if server_type == 'Apache':
        shl('systemctl stop apache2')
    elif server_type == 'Nginx':
        shl('systemctl stop nginx')

def extract_archive_to_site(archive_path, site_name):
    '''Распаковывает архив в директорию сайта'''
    dir_site = f'/var/www/{site_name}'

    # Создание директории если ее не существует
    shl(f'mkdir -p {dir_site}')

    try:
        with zipfile.ZipFile(archive_path, 'r') as zip_archive: # Распаковка zip файла в dir_site
            zip_archive.extractall(dir_site)
        return True, f'Файлы успешно распакованы в {dir_site}'
    except Exception as e:
        return False, f'Ошибка при распаковке: {str(e)}'

def certbot_setup(server_type, domain): # Demo функция
    if shutil.which('certbot'):
        print('Установка certbot')
        shl('apt update -y')
        shl('apt install certbot python3-certbot -y')

    shl('ufw allow 443/tcp') # открытие порта для https

    if server_type == 'Apache':
        shl('apt install python3-certbot-apache -y')
        shl(f'certbot --apache -d {domain} -d www.{domain}')
        shl('apachectl configtest')
        shl('sudo systemctl reload apache2')

    elif server_type == 'Nginx':
        shl('apt install python3-certbot-nginx -y')
        shl(f'certbot --nginx -d {domain} -d www.{domain}')
        shl('nginx -t')
        shl('systemctl reload nginx')

