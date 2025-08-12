import asyncio
from telethon import TelegramClient, events
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from secrets import config


async def poll_once():
    client = TelegramClient('session', config.API_ID, config.API_HASH)
    await client.start(phone=config.PHONE_NUMBER)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_FILE, scope)
    gclient = gspread.authorize(creds)
    sheet = gclient.open_by_key(config.SPREADSHEET_ID).sheet1

    statuses = []

    for number in config.CAR_NUMBERS:
        await client.send_message(config.BOT_USERNAME, number)
        response_text = None

        @client.on(events.NewMessage(from_users=config.BOT_USERNAME))
        async def handler(event):
            nonlocal response_text
            response_text = event.message.text.strip()
            client.remove_event_handler(handler)

        # Ждём до 5 секунд ответа
        for _ in range(10):
            await asyncio.sleep(0.5)
            if response_text:
                break

        status = "Нет ответа"
        if response_text:
            if "от" in response_text:
                try:
                    date_str = response_text.split("от")[-1].strip()
                    last_seen = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
                    delta = datetime.now() - last_seen
                    status = "На связи" if delta.total_seconds() <= 3600 else "Нет связи"
                except ValueError:
                    status = "Ошибка даты"
            else:
                status = "Формат неизвестен"

        statuses.append(status)

    await client.disconnect()

    # Добавляем новый столбец в Google Sheets
    current_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    new_col = [current_time_str] + statuses
    sheet.insert_cols([new_col], 2)


async def main_loop():
    while True:
        print(f"[{datetime.now()}] Запуск опроса...")
        await poll_once()
        print(f"[{datetime.now()}] Опрос завершён. Ждём {config.POLL_INTERVAL_MINUTES} минут.")
        await asyncio.sleep(config.POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main_loop())
