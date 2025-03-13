FROM python:3.11-alpine

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . .

# RUN pip freeze > requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Открываем порт
EXPOSE 8000

# Запускаем сервер для FastAPI
CMD ["uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
