FROM python:3.11-slim

WORKDIR /project

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN flake8 app

CMD ["python", "app/main.py"]