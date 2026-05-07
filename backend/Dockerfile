FROM python:3.11-slim

# Hugging Face Spaces requires running as a non-root user
RUN useradd -m -u 1000 user

ENV PYTHONUNBUFFERED=True \
    PORT=7860 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container and set permissions
COPY --chown=user:user . .

# Switch to the "user" user
USER user

# Hugging Face Spaces listens on port 7860 by default
EXPOSE 7860

# Run the web service using gunicorn
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
