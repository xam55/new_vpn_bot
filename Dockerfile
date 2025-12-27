FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    openssh-client \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код
COPY . .

# Папки
RUN mkdir -p /app/data/database /app/logs /app/static

# Запуск
CMD ["python", "run.py"]
