# Вихідний образ з Python
FROM python:3.12-slim

# Встановлюємо залежності для компіляції Python-пакетів
# RUN apt-get update && apt-get install -y \
#     gcc \
#     libpq-dev \
#     build-essential \
#     python3-dev \
#     && rm -rf /var/lib/apt/lists/*
    
# Встановлюємо робочу директорію всередині контейнера
WORKDIR /app

# Копіюємо файли з поточної директорії (context) в контейнер
COPY . .

# Встановлюємо залежності (якщо є requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Команда запуску (рекомендовано для FastAPI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]