import asyncio
from telethon import TelegramClient, events
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from telethon.errors import FloodWaitError
import random

# Загружаем переменные окружения
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


def col_number_to_letter(n):
    """Преобразует номер колонки в букву (1 -> A, 2 -> B, ...)"""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def insert_column_shift_right(spreadsheet, insert_index=1):
    """Вставляет пустой столбец, сдвигая все остальные вправо"""
    sheet = spreadsheet.get_worksheet(0)
    sheet_id = sheet.id

    body = {
        "requests": [{
            "insertDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": insert_index,
                    "endIndex": insert_index + 1
                },
                "inheritFromBefore": False
            }
        }]
    }

    print(f"sheet_id: {sheet_id}")
    print(f"Request body: {body}")

    spreadsheet.batch_update(body)
    print("Столбец успешно вставлен")


async def poll_once():
    print("Запускается опрос...")

    client = TelegramClient('sessions/session', API_ID, API_HASH)
    try:
        await client.start(phone=PHONE_NUMBER)
    except FloodWaitError as e:
        print(f"Ждем {e.seconds} секунд из-за ограничения Telegram...")
        await asyncio.sleep(e.seconds)
        await client.start(phone=PHONE_NUMBER)

    # Авторизация Google Sheets
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
    gclient = gspread.authorize(creds)
    spreadsheet = gclient.open_by_key(SPREADSHEET_ID)

    statuses = []

    async def get_response(number):
        nonlocal client
        response_text = None

        @client.on(events.NewMessage(from_users=BOT_USERNAME))
        async def handler(event):
            nonlocal response_text
            if event.message.message.startswith(f"ГРЗ: {number}"):
                response_text = event.message.text.strip()
                client.remove_event_handler(handler)

        await client.send_message(BOT_USERNAME, number)

        for _ in range(20):
            await asyncio.sleep(0.5)
            if response_text:
                break

        if not response_text:
            return "Нет ответа"

        if "Слишком много запросов" in response_text:
            print(f"{number} — Слишком много запросов. Ждем 15 секунд...")
            await asyncio.sleep(15)
            return await get_response(number)

        try:
            date_str = response_text.split("от")[-1].strip()
            last_seen = datetime.strptime(date_str, "%d-%m-%Y %H:%M:%S")
            delta = datetime.now() - last_seen
            if delta.total_seconds() <= 3600:
                return "🟢 На связи"
            else:
                return "🔴 Нет связи"
        except Exception:
            return "Ошибка формата"

    total_requests = len(CAR_NUMBERS)

    for i, number in enumerate(CAR_NUMBERS, start=1):
        response_text = await get_response(number)
        wait_time = random.randint(6, 10)
        print(f"Ждем {wait_time} секунд перед следующим запросом... {i}/{total_requests} Текущий запрос: {number} Ответ: {response_text}")
        statuses.append(response_text)
        await asyncio.sleep(wait_time)

    await client.disconnect()

    current_time_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Вставляем пустой столбец на место B
    insert_column_shift_right(spreadsheet, insert_index=1)

    # Обновляем лист после вставки
    sheet = spreadsheet.get_worksheet(0)

    # Заполняем B1 датой, а ниже — статусами
    new_col = [current_time_str] + statuses
    col_letter = col_number_to_letter(2)  # B
    cell_range = f"{col_letter}1:{col_letter}{len(new_col)}"
    sheet.update(cell_range, [[item] for item in new_col])

    print(f"Опрос завершён в {current_time_str}")


async def main():
    while True:
        await poll_once()
        print(f"Ожидаем {POLL_INTERVAL_MINUTES} минут до следующего опроса...")
        await asyncio.sleep(POLL_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main())
