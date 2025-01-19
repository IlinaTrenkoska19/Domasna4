# Избери основен image за Python 3.12
FROM python:3.12

# Креирај работен директориум во контейнерот
WORKDIR /app

# Копирај го кодот од локалниот компјутер во контейнерот
COPY . /app

# Инсталирај ги зависностите од `requirements.txt`
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5002

# Постави командата што ќе се изврши кога контейнерот ќе стартува
CMD ["python", "app.py"]
