# work_for_ssh.py

import subprocess



def shl(cmd):
    '''Отправка команд в консоль shell=True, capture_output=True, text=True'''
    print(f'Выполнение команды: {cmd}')
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Ошибка команды {cmd}: {result.stderr}")
        return result
    else:
        return result

def get_config(a):
        '''Определяет состояние конфига путем проверки файла sshd_config'''
        try:
            with open("/etc/ssh/sshd_config", 'r', encoding = 'utf-8') as file:
                for line in file:
                    if line.startswith(f'{a}') or line.startswith(f'#{a}'):
                        output = line.split(' ', 1)[1].strip().strip('"')
                        return output
        except:
            return None
        

def changesshport(port=2222):
    '''Меняет ssh порт'''
    try:
        with open("/etc/ssh/sshd_config", 'r', encoding = 'utf-8') as file:
            lines = file.readlines()

        with open("/etc/ssh/sshd_config", 'w', encoding = 'utf-8') as file:
            confirm = False
            for line in lines:
                if line.strip().startswith('Port') or line.strip().startswith('#Port'):
                    file.write(f'Port {port}\n')
                    print(f'Порт ssh сменен. \n {port}')
                    confirm = True
                else:
                    file.write(line)
            if confirm is False:
                file.write(f'\nPort {port}\n')
        return 1
    except Exception as e: 
        print(e)
        return 0


def downloadUFW(y=True):
    '''Установка UFW'''
    try:
        print('Проверка установки ufw...')
        try:
            print('Устанавливаю ufw...')
            shl('apt install ufw -y')
        except Exception as e:
            print(e)
        if y:
            shl('ufw allow ssh') # По умолчанию разрешаем ssh
        shl('echo "y" | sudo ufw enable')
    except Exception as e:
        print(e)


def changeuserpasswd(user, passwd):
    '''Меняет пароль пользователя'''
    try:
        shl(f'echo "{user}:{passwd}" | sudo chpasswd')
    except Exception as e:
        print(f'Ошибка {e}')


def sshkey(user='root'):
    '''Создание ssh ключа'''
    try:
        if user == 'root':
            homedir = f"/root"
        else:
            homedir = f"/home/{user}"

        shl(f'mkdir -p {homedir}/.ssh')


        shl(f'chmod 700 {homedir}/.ssh')
        shl(f'ssh-keygen -t ed25519 -f {homedir}/.ssh/id_ed25519 -N "" -q')
        shl(f'cat {homedir}/.ssh/id_ed25519.pub >> {homedir}/.ssh/authorized_keys')
        shl(f'chmod 600 {homedir}/.ssh/authorized_keys')
        print(f'Ключ создан и добавлен к пользователю {user}')
    except Exception as e:
        print(f'Ошибка {e}')


def rootnologin(y=0):
    '''Запрещает заходить под root'''
    try:
        with open("/etc/ssh/sshd_config", 'r', encoding = 'utf-8') as file:
            lines = file.readlines()

        with open("/etc/ssh/sshd_config", 'w', encoding = 'utf-8') as file:
            confirm = False
            if y == 0:
                y = 'no'
            else:
                y = 'yes'
            for line in lines:
                if line.strip().startswith('PermitRootLogin') or line.strip().startswith('#PermitRootLogin'):
                    file.write(f'PermitRootLogin {y}\n')
                    print(f'Возможность входа root по паролю теперь {y}')
                    confirm = True
                else:
                    file.write(line)
            if confirm is False:
                file.write(f'\nPermitRootLogin {y}\n')
        return 1
    except Exception as e:
        print(e)
        return 0


def passwdnologin(y=0):
    '''Меняет ssh порт'''
    try:
        with open("/etc/ssh/sshd_config", 'r', encoding = 'utf-8') as file:
            lines = file.readlines()

        with open("/etc/ssh/sshd_config", 'w', encoding = 'utf-8') as file:
            confirm = False
            if y == 0:
                y = 'no'
            else:
                y = 'yes'
            for line in lines:
                if line.strip().startswith('PasswordAuthentication') or line.strip().startswith('#PasswordAuthentication'):
                    file.write(f'PasswordAuthentication {y}\n')
                    print(f'Возможность входа по паролю теперь {y}')
                    confirm = True
                else:
                    file.write(line)
            if confirm is False:
                file.write(f'\nPort {y}\n')
        return 1
    except Exception as e:
        print(e)
        return 0


def downlfail2ban():
    '''Установка fail2ban'''
    try:
        print('Устанавливаю fail2ban...')
        try:
            shl('apt install fail2ban -y')
        except Exception as e:
            print(e)
        shl('systemctl start fail2ban')
        shl('systemctl enable fail2ban')
    except Exception as e:
        print(e)

def updatesystem():
    '''Обновляет систему используя apt'''
    print('Обновление системы...')
    shl('apt update -y')
    shl('apt upgrade -y')
    shl('apt dist-upgrade -y')
    shl('apt autoremove -y')
    shl('apt autoclean -y')
    print('Обновление завершено!')

