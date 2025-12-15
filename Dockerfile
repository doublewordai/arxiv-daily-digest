# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY *.py .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Run the script
CMD ["python", "main.py"]