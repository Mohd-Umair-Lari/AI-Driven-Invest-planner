FROM python:3.11-slim

RUN useradd -m -u 1000 user

ENV PYTHONUNBUFFERED=True \
    PORT=7860 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies from the backend folder
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the backend code to the container
COPY --chown=user:user backend/ .

USER user

EXPOSE 7860

CMD exec uvicorn server:asgi_app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --loop asyncio \
    --timeout-keep-alive 75
