try:
    import platform
    import subprocess
    import os
    import shutil
    from pathlib import Path

    print('Спасибо, что скачали EasySetBot! Перед началом рекомендую создать бота у @BotFather и сохранить его токен.')
    print('Если вам понравился ESBot, поставьте, пожалуйста, звезду или напишите комментарий на GitHub!')

    try:
        if os.geteuid() != 0: # Проверка на права root
            print("Требуются права root! Запустите скрипт с sudo.")
            exit(1)
    except Exception as e:
        print(f'Не удалось определить права root: {e}')


    def get_distro():
        '''Определяет дистрибутив Linux путем проверки файла os-release'''
        try:
            with open("/etc/os-release", 'r', encoding = 'utf-8') as file:
                for line in file:
                    if line.startswith('ID='):
                        distro = line.split('=', 1)[1].strip().strip('"')
                        return distro
        except:
            return None

    def shl(cmd):
        '''Отправляет команды в консоль shell=True, capture_output=True, text=True'''
        print(f'Выполнение команды: {cmd}')
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка команды {cmd}: {result.stderr}")
            return result
        else:
            return result

    def endwitherror():
        print('Попытка удаления...')
        try:
            shl('pkill -u ESBot')
        except Exception as e:
            print(f'Попытка завершить процессы пользователя ESBot: {e}')

        try:
            shl('userdel -r ESBot')
        except Exception as e:
            print(f'Попытка удалить пользователя ESBot: {e}')

        try:
            shl('rm -rf /home/ESBot')
        except Exception as e:
            print(f'Попытка удалить директорию пользователя ESBot {e}')

        try:
            shl('systemctl stop esbot')
        except Exception as e:
            print(f'Попытка завершить работу службы esbot {e}')
        exit(1)

    print('Введите телеграм токен.')
    print('Его можно получить у @BotFather в телеграм')
    print('Токен выглядит вот так:')
    print('1234567890:ABCDEFGhijKLMNopqrstUVWXYZ-abcdefg')
    token = str(input()).strip()

    if not token:
        print("Токен не может быть пустым!")
        print('Введите телеграм токен.')
        token = str(input()).strip()

        if not token:
            print("Токен не может быть пустым!")
            exit(1)

    print('Не передавайте ваш токен и храните его в безопасном месте. Он - ключ к вашему боту.')

    system = platform.system() # Определение системы
    print(f'Ваша система - {system}')

    if system == 'Linux':
        distribution = get_distro() # Попытка определения дистрибутива

        print(f'Ваш дистрибутив: {distribution}')

        if distribution == 'ubuntu' or distribution == 'debian':
            try:
                try:

                    if shl("id ESBot").returncode == 0:
                        print("Пользователь ESBot уже существует")
                        print('Хотите переустановить бота? (да/нет)')
                        if input().lower() == 'да':
                            endwitherror()
                            print('Перезапустите установщик!')
                        exit(1)

                except:
                    pass
                print('Создание пользователя...')
                shl('useradd -m -s /usr/sbin/nologin ESBot') # Добавление user ESBot

                if shutil.which('sudo') is None: # Скачивание sudo если его нет
                    shl('apt install sudo -y')

                shl('usermod -aG sudo ESBot') # Добавление ESBot в sudo

                print('Начинаю установку пакета под Ubuntu / Debian.')
                if Path('EasySetBot').exists(): # Проверка установки
                    print('Ошибка установки. Папка EasySetBot существует. Скорее всего установка уже была выполнена.')
                    print('Хотите переустановить бота? (да/нет)')
                    if input().lower() == 'да':
                        endwitherror()
                        print('Перезапустите установщик!')
                    print('Завершаю работу.')
                    exit(1)

                else:
                    print('Обновление пакетов')
                    shl('sudo apt update -y')
                    print('Скачиваю vnstat')
                    shl(f'apt install -y vnstat')
                    if shutil.which('git') is None: # Скачивание git если его нет
                        print('Устанавливаю git...')
                        shl('sudo apt install git -y')
                    downloadlink = 'https://github.com/Danik1087/EasySetBot/releases/download/v0.7/' # Ссылка скачивания репозитория.
                    shl("sudo -u ESBot mkdir -p /home/ESBot/EasySetBot") # Создание директории телеграм-бота
                    print(f'Начинаю установку с \n{downloadlink}')
                    files = [
                        "firstload.py",
                        "libraries.zip",
                        "main.py",
                        "requirements.txt",
                        "users.json"
                    ]
                    try:
                        for file in files:
                            shl(f'sudo -u ESBot wget -q -O /home/ESBot/EasySetBot/{file} {downloadlink+file}')

                    except Exception as e:
                        print('Установка остановлена с ошибкой.')
                        print(e)
                        endwitherror()
                            



                    print('Начинаю преднастройку телеграм-бота.')
                    if shutil.which('pip3') is None: # установка pip
                        print('Устанавливаю pip...')
                        shl('sudo apt install python3-pip -y')
                    print('Создаю окружение...')
                    print('Устанавливаю python3-venv...')
                    shl('sudo apt install -y python3-venv')
                    venv_path = '/home/ESBot/EasySetBot/ESBotvenv'
                    shl(f'sudo -u ESBot python3 -m venv {venv_path}') # создание окружения

                    venv_pip = f'{venv_path}/bin/pip'
                    python_path = f'{venv_path}/bin/python'
                    shl(f'{venv_pip} install --upgrade pip')
                    try:
                        shl(f'{venv_pip} install -r /home/ESBot/EasySetBot/requirements.txt')
                    except Exception as e:
                        print(f'Ошибка \n{e}')
                    shl('sudo -u ESBot touch /home/ESBot/EasySetBot/.env')
                    with open('/home/ESBot/EasySetBot/.env', 'w',  encoding = 'utf-8') as file:
                        file.write(f'TOKEN={token}')
                    # Запуск основного проекта
                    subprocess.run(f'{python_path} /home/ESBot/EasySetBot/firstload.py', shell=True, capture_output=False, text=True)





            except Exception as e:
                print(f'Ошибка: {e}')
                print(f'Процесс завершен с ошибкой.')
                endwitherror()

        else:
            print('Дистрибутив не поддерживается. Поддерживаются только: \n Ubuntu \n Debian')

    else:
        print('Операционная система не поддерживается. Поддерживаются только: \n Linux Ubuntu \n Linux Debian')

except KeyboardInterrupt:
    print("\nУстановка прервана пользователем")
    endwitherror()

except Exception as e:
    print(f"Критическая ошибка: {e}")
    print(f'Процесс завершен с ошибкой.')
    endwitherror()


