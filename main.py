import asyncio
from telethon import TelegramClient, events
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
BOT_USERNAME = os.getenv("BOT_USERNAME")

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")

CAR_NUMBERS = [
    "А410НС702", "В582АО702", "К197МН702", "К873МК702", "В634ОХ702",
    "К775КА702", "К993ЕУ702", "А082СВ702", "А092ОВ702", "А142СВ702",
    "А145НС702", "А529ОС702", "А990ХМ702", "В038АН702", "В589АН702",
    "В607АУ702", "К012ММ702", "К438ЕС702", "К556ЕС702", "К619КА702",
    "К849ЕУ702", "М509КВ702", "А459АС702", "Р145УЕ102", "Р146УЕ102",
    "Р400КХ102", "Р575МС102", "Т710ОА102", "У407ХН102", "У410ОА102",
    "У428ХН102", "У490ОА102", "Х472ОС102", "Х592ТР102"
]

POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", 10))


async def poll_once():
    print("Запускается опрос...")
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    gclient = gspread.authorize(creds)
    sheet = gclient.open_by_key(SPREADSHEET_ID).sheet1

    statuses = []

    async def get_response(number):
        response_text = None

        @client.on(events.NewMessage(from_users=BOT_USERNAME))
        async def handler(event):
            nonlocal response_text
            if event.message.message.startswith(f"ГРЗ: {number}"):
                response_text = event.message.text.strip()
                client.remove_event_handler(handler)

        await client.send_message(BOT_USERNAME, number)

        for _ in range(20):  # ждём до 10 секунд (20 * 0.5)
            await asyncio.sleep(0.5)
            if response_text:
                break

        if not response_text:
            return "Нет ответа"

        try:
            date_str = response_text.split("от")[-1].strip()
            last_seen = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
            delta = datetime.now() - last_seen
            if delta.total_seconds() <= 3600:
                return "На связи"
            else:
                return "Нет связи"
        except Exception:
            return "Ошибка формата"

    tasks = [get_response(number) for number in CAR_NUMBERS]
    results = await asyncio.gather(*tasks)

    statuses.extend(results)

    await client.disconnect()

    current_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    new_col = [current_time_str] + statuses
    sheet.insert_cols([new_col], 2)
    print(f"Опрос завершён в {current_time_str}")


async def main():
    while True:
        await poll_once()
        print(f"Ожидаем {POLL_INTERVAL_MINUTES} минут до следующего опроса...")
        await asyncio.sleep(POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main())
