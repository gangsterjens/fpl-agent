FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY data/credentials.json /app/data/credentials.json


CMD ["python", "run.py"]
