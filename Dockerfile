FROM python:3.11-slim

WORKDIR /app

# System deps you might need (optional):
# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Optional, but nice for clarity:
EXPOSE 8080

# Start FastAPI via Uvicorn on Fly's expected port
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
