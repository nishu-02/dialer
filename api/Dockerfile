FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME /data
ENV DB_PATH=/data/dialer.db

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
