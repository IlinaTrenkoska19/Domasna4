# 1. Користи основен image (на пример Python)
FROM python:3.12

# 2. Постави работен директориум во контејнерот
WORKDIR /app

# 3. Копирај ги само requirements.txt во контејнерот
COPY requirements.txt /app/

# 4. Инсталирај ги зависностите
RUN pip install --no-cache-dir -r requirements.txt

# 5. Копирај го целиот код во контејнерот
COPY . /app/

# 6. Дефинирај која порта ја користи апликацијата
EXPOSE 5001

# 7. Дефинирај командата за стартување на апликацијата
CMD ["python", "app.py"]
