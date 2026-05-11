FROM python:3.11-slim

RUN useradd -m -u 1000 user

ENV PYTHONUNBUFFERED=True \
    PORT=7860 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user:user . .

USER user

EXPOSE 7860

CMD exec uvicorn main:asgi_app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --loop asyncio \
    --timeout-keep-alive 75
