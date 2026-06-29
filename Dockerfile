# Используем стабильный легковесный образ питона
FROM python:3.12-slim

# Устанавливаем системные зависимости, необходимые для сборки некоторых пакетов (например, psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Задаем рабочую директорию внутри контейнера
WORKDIR /app

# Запрещаем питону писать файлы .pyc на диск и включаем моментальный вывод логов в консоль
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем и устанавливаем зависимости
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в контейнер
COPY . /app/

# Открываем порт, на котором обычно крутится Django
EXPOSE 8000

# Стандартная команда для запуска (пока оставим runserver, потом заменим на gunicorn)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]