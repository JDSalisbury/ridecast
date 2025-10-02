# Use Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run uvicorn on port 8080 (Fly expects 8080 by default)
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
