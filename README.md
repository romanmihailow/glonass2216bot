# glonass2216bot

Бот для автоматического опроса Telegram-бота с госномерами автомобилей и записи результатов в Google Sheets.

## Возможности
- Подключение к Telegram через [Telethon](https://docs.telethon.dev/).
- Чтение/запись данных в Google Sheets через [gspread](https://docs.gspread.org/).
- Автоматическая вставка нового столбца **B** с датой и результатами опроса.
- Обработка ошибок Telegram API (FloodWaitError).
- Гибкая настройка через `.env`.
- Поддержка Docker с сохранением сессий и секретов.

## Требования
- Python 3.12+
- Доступ к Google API (JSON ключ сервисного аккаунта)
- Доступ к Telegram API (API ID, API Hash, номер телефона)

## Установка и запуск без Docker
```bash
git clone <repo_url>
cd glonass2216bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
