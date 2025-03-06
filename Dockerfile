FROM python:3.11-slim

WORKDIR /app

# Встановлення залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіювання коду
COPY . .

# Змінні середовища
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Порт на якому буде запущено сервіс
EXPOSE $PORT

# Запуск додатку
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
