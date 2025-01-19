# Почни од Python 12 image
FROM python:3.12-slim

# Постави работна папка во контејнерот
WORKDIR /app

# Копирај ги сите датотеки во работната папка
COPY . /app

# Инсталирај ги зависностите од requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Отвори го портот 5003 за комуникација
EXPOSE 5003

# Команда за стартирање на апликацијата
CMD ["python", "app.py"]
