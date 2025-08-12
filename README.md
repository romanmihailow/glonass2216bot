# Glonass Checker

## Описание
Сервис для опроса Telegram-бота @Glonass2216_bot по списку госномеров и записи статусов в Google Sheets.

## Настройка

1. Создайте `.env` с нужными значениями.
2. Положите JSON ключ Google в `secrets/`.
3. Запустите:

```bash
docker-compose up -d --build
