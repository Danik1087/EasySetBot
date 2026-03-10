# EasySetBot
Telegram Bot - Ubuntu/Debian Server Control Panel

##⚡️Быстрый запуск
'''curl -s https://github.com/Danik1087/EasySetBot/releases/download/v0.8/installer.py | python3'''

## 🚀 Функции
 - Мониторинг сервера (CPU, RAM, трафик, скорость интернета)
 - Менеджер ssh конфигурации
 - Скачивание/загрузка файлов
 - Консоль удаленного доступа
 - Управление Apache/Nginx
 - Авторизация по паролю и Telegram айди

## 📦 Установка
 - Скачать Python 
 (sudo apt install python3 -y)
 - Скачать и запустить установщик
 (sudo python3 installer.py)
 - Следовать инструкциям установщика:
   - Ввести свой токен Телеграм-бота
   - Отправить любое сообщение вашему боту
   - Сохранить пароль

## ⚠️ Важное
 - Сервис запрашивает полные права на устройстве (root доступ). Это необходимо для работы. Вы можете ознакомиться с открытым кодом.
 - Сервис запрашивает токен Telegram бота. Токен необходим для работы бота. Токен надёжно хранится локально на устройстве и не передается третьим лицам.
 - Сервис предоставляет услуги удаленного доступа. Используйте только в легальных целях!

## 📄 Лицензия
 - Код сервиса открыт и распространяется под лицензией MIT. Вы можете свободно использовать его при условии указания авторства.

## 🚫 Удаление
 - Вы можете удалить сервис, запустив установщик, и нажав ctrl c
 - Ручное удаление включает в себя:
   - Принудительное завершение всех процессов пользователя esbot
   - Удаление пользователя esbot
   - Остановка службы esbot
   - Удаление службы esbot

## ❓ Часто задаваемые вопросы 
 - Бот не отвечает на команды:
  1. Подождите в течении 4 - 10 минут. Возможно вы поставили на установку что-либо, и сервис сейчас занят этим.
  2. Проверьте статус службы esbot (sudo systemctl status esbot) и перезапустите (sudo systemctl restart esbot)

## English (machine-translated)

##⚡️Quick start
‘’'curl -s https://github.com/Danik1087/EasySetBot/releases/download/v0.8/installer.py | python3'‘’

## 🚀 Features
 - Server monitoring (CPU, RAM, traffic, internet speed)
 - SSH configuration manager
 - File download/upload
 - Remote access console
 - Apache/Nginx management
 - Password and Telegram ID authorization

## 📦 Installation
 - Download Python 
 (sudo apt install python3 -y)
 - Download and run the installer
 (sudo python3 installer.py)
 - Follow the installer instructions:
   - Enter your Telegram bot token
   - Send any message to your bot
   - Save your password

## ⚠️ Important
 - The service requests full rights on the device (root access). This is necessary for it to work. You can view the open source code.
 - The service requests a Telegram bot token. The token is necessary for the bot to work. The token is securely stored locally on the device and is not transferred to third parties.
 - The service provides remote access services. Use only for legal purposes!

## 📄 License
 - The service code is open source and distributed under the MIT license. You are free to use it provided that you indicate the authorship.

## 🚫 Removal
- You can remove the service by running the installer and pressing ctrl c
- Manual removal includes:
  - Forcibly terminating all esbot user processes
  - Deleting the esbot user
  - Stopping the esbot service
  - Removing the esbot service

## ❓ Frequently asked questions 
- The bot does not respond to commands:
  1. Wait for 4-10 minutes. You may have set something up, and the service is currently busy with it.
  2. Check the status of the esbot service (sudo systemctl status esbot) and restart it (sudo systemctl restart esbot).
