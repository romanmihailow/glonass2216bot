# Используем официальный образ Python
FROM python:3.12-slim

# Установим рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы проекта
COPY . /app/

# Устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Точка входа
CMD ["python", "main.py"]
