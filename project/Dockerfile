# Користиме Python 3.12 со slim-базирана слика
FROM python:3.12-slim

# Инсталирај основни алатки и python3-distutils (потребно за изградба на зависности)
RUN apt-get update && apt-get install -y \
    python3-distutils \
    build-essential \
    gcc \
    && apt-get clean

# Ажурирај го pip, setuptools и wheel за сигурна изградба на Python пакети
RUN pip install --upgrade pip setuptools wheel

# Копирај го `requirements.txt` во контејнерот
COPY requirements.txt .

# Инсталирај ги сите зависности од `requirements.txt`
RUN pip install --no-cache-dir -r requirements.txt

# Копирај го остатокот од проектот во контејнерот
COPY . /app

# Постави го работниот директориум
WORKDIR /app

# Експонирај порта ако е потребно (замени 5000 со порта на твојата апликација)
EXPOSE 5000

# Дефинирај ја командата за стартување на апликацијата
CMD ["python", "app.py"]
