
try:
    from time import sleep
    from random import randint
    import subprocess
    import os
    try:
        from dotenv import load_dotenv
        from telegram import Update # запуск бота 
        from telegram.ext import (
            Application,          # Ядро бота
            ContextTypes,         # Обработчик кнопок
            MessageHandler,       # Обработчик сообщений
            filters
        )

    except Exception as e:
        print(f'Ошибка импорта библиотек! {e}')
    
    def passwd(a):
        password = str()
        alltext = "1234567890"
        for i in range(a):
            password = password + alltext[randint(0, len(alltext)-1)]
        return password

    def shl(cmd):
        '''Отправляет команды в консоль shell=True, capture_output=True, text=True'''
        print(f'Выполнение команды: {cmd}')
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка команды {cmd}: {result.stderr}")
            return result
        else:
            return result
    load_dotenv()
    token = os.getenv('TOKEN')
    application = Application.builder().token(token).build()

    async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.message.from_user
        text = update.message.text
        chat = update.effective_chat
        await update.message.reply_text(f"{text}")
        response = (
                f"ID: `{user.id}`\n"
                f"Имя: {user.first_name}\n"
                f"Фамилия: {user.last_name or '❌'}\n"
                f"Юзернейм: @{user.username or 'не указан'}\n"
                f"Язык: {user.language_code or 'не указан'}\n"
                f"Бот: {'✅' if user.is_bot else '❌'}\n"
                f"Тип чата: {chat.type}\n"
                f"Отправка: {text}\n"
            )
        print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n')
        print(' !!! Проверьте вы ли это. Если это не вы нажмите ctrl c')
        print(response)
        print('Скрипт не завис! Подождите немного.')
        sleep(15)
        ID1 = user.id
        password = passwd(4)
        warning_msg = await update.message.reply_text(
            "После получения пароля скопируйте его ведь он будет удален через 15 секунд. \nЕсли вы не успели скопировать пароль, то он будет в терминале сервера."
        )
        
        passwd_msg = await update.message.reply_text(f"Ваш пароль:\n{password}")
        print(f'Ваш пароль:\n{password}')
        sleep(15)
        try:
            await warning_msg.delete()
            await passwd_msg.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщения: {e}")
        
        shl('touch /home/ESBot/EasySetBot/.env')
        with open('/home/ESBot/EasySetBot/.env', 'w',  encoding = 'utf-8') as file:
            file.write(f'TOKEN={token}\n')
            file.write(f'ADMIN={ID1}\n')
            file.write(f'PASSWORDADM={password}\n')
        print('Бот остановлен.')
        print('Начинаю создание службу через systemd')
        shl('touch /etc/systemd/system/esbot.service')

        servicetxt = ('''[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ESBot/EasySetBot
ExecStart=/home/ESBot/EasySetBot/ESBotvenv/bin/python /home/ESBot/EasySetBot/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
MemoryLimit=256M
CPUQuota=50%

[Install]
WantedBy=multi-user.target''')

        with open('/etc/systemd/system/esbot.service', 'w',  encoding = 'utf-8') as file:
            file.write(servicetxt)
        shl('systemctl daemon-reload')
        shl('systemctl enable esbot.service')
        shl('systemctl start esbot.service') 
        print('Возможна ошибка. Некритичная')
        exit(1)

    application.add_handler(MessageHandler(filters.TEXT, text_handler))
    print('Бот запущен. Запустите и отправьте ему любое сообщение.')
    application.run_polling()
    
except Exception as e:
    print(f'КРИТИЧЕСКАЯ ОШИБКА \n {e}')
