FROM python:3.11-alpine

WORKDIR /dgg-logger
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser -D appuser
RUN mkdir -p /dgg-logger/logs && chown -R appuser:appuser /dgg-logger/logs
USER appuser

ENTRYPOINT ["python", "main.py"]