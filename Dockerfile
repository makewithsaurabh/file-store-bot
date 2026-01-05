FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY filestore_bot.py .
COPY bot_messages.json .

# Create directory for cache
RUN mkdir -p /app/data

# Run the bot
CMD ["python", "filestore_bot.py"]
