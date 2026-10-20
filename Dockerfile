FROM python:3.12-alpine

# Install rclone, CA certificates for TLS/SSL, and timezone data
RUN apk add --no-cache rclone ca-certificates tzdata

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Ensure output streams are unbuffered for Docker logging
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]
