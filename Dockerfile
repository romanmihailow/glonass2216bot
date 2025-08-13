# Используем официальный образ Python
FROM python:3.12-slim

# Установим рабочую директорию
WORKDIR /app

# Копируем все файлы проекта
COPY . /app/

# Создаем папку для сессий
RUN mkdir -p /app/sessions

# Устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Точка входа
CMD ["python", "main.py"]
