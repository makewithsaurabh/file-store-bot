# 🚀 Deployment Guide

This guide covers various deployment options for the File Storage Bot.

## Table of Contents

- [VPS/Server Deployment](#vpsserver-deployment)
- [Heroku Deployment](#heroku-deployment)
- [Railway Deployment](#railway-deployment)
- [Docker Deployment](#docker-deployment)
- [Render Deployment](#render-deployment)

---

## VPS/Server Deployment

### Prerequisites
- Ubuntu/Debian server with SSH access
- Python 3.8+ installed
- Git installed

### Steps

1. **Connect to your server**
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Python and dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip git screen -y
   ```

3. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/file-store-bot.git
   cd file-store-bot
   ```

4. **Install Python dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Configure the bot**
   ```bash
   nano filestore_bot.py
   # Edit BOT_TOKEN, channel IDs, and admin IDs
   ```

6. **Run the bot in background**
   ```bash
   screen -S filebot
   python3 filestore_bot.py
   # Press Ctrl+A, then D to detach
   ```

7. **Reattach to screen** (to check logs)
   ```bash
   screen -r filebot
   ```

### Auto-restart on Reboot

Create a systemd service:

```bash
sudo nano /etc/systemd/system/filebot.service
```

Add:

```ini
[Unit]
Description=Telegram File Storage Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/file-store-bot
ExecStart=/usr/bin/python3 /path/to/file-store-bot/filestore_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable filebot
sudo systemctl start filebot
sudo systemctl status filebot
```

---

## Heroku Deployment

### Prerequisites
- Heroku account
- Heroku CLI installed

### Steps

1. **Login to Heroku**
   ```bash
   heroku login
   ```

2. **Create a new app**
   ```bash
   heroku create your-bot-name
   ```

3. **Set environment variables**
   ```bash
   heroku config:set BOT_TOKEN=your_bot_token
   heroku config:set FILES_CHANNEL_ID=-1001234567890
   heroku config:set LOGS_CHANNEL_ID=-1001234567890
   heroku config:set BACKUP_CHANNEL_LINK=https://t.me/your_channel
   heroku config:set ADMIN_USER_IDS=123456789
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Scale the worker**
   ```bash
   heroku ps:scale worker=1
   ```

6. **Check logs**
   ```bash
   heroku logs --tail
   ```

---

## Railway Deployment

### Steps

1. **Go to [Railway.app](https://railway.app)**

2. **Create new project** → Deploy from GitHub

3. **Select your repository**

4. **Add environment variables** in Railway dashboard:
   - `BOT_TOKEN`
   - `FILES_CHANNEL_ID`
   - `LOGS_CHANNEL_ID`
   - `BACKUP_CHANNEL_LINK`
   - `ADMIN_USER_IDS`

5. **Deploy** - Railway will automatically detect Python and deploy

6. **Monitor logs** in Railway dashboard

---

## Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose (optional)

### Using Docker

1. **Build the image**
   ```bash
   docker build -t file-store-bot .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     --name filebot \
     -e BOT_TOKEN=your_token \
     -e FILES_CHANNEL_ID=-1001234567890 \
     -e LOGS_CHANNEL_ID=-1001234567890 \
     -e BACKUP_CHANNEL_LINK=https://t.me/channel \
     -e ADMIN_USER_IDS=123456789 \
     --restart unless-stopped \
     file-store-bot
   ```

3. **Check logs**
   ```bash
   docker logs -f filebot
   ```

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  filebot:
    build: .
    container_name: file-store-bot
    restart: unless-stopped
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - FILES_CHANNEL_ID=${FILES_CHANNEL_ID}
      - LOGS_CHANNEL_ID=${LOGS_CHANNEL_ID}
      - BACKUP_CHANNEL_LINK=${BACKUP_CHANNEL_LINK}
      - ADMIN_USER_IDS=${ADMIN_USER_IDS}
    volumes:
      - ./data:/app/data
```

Run:

```bash
docker-compose up -d
```

---

## Render Deployment

### Steps

1. **Go to [Render.com](https://render.com)**

2. **Create new Web Service** → Connect GitHub repository

3. **Configure**:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python filestore_bot.py`

4. **Add environment variables** in Render dashboard:
   - `BOT_TOKEN`
   - `FILES_CHANNEL_ID`
   - `LOGS_CHANNEL_ID`
   - `BACKUP_CHANNEL_LINK`
   - `ADMIN_USER_IDS`

5. **Deploy** - Render will automatically build and deploy

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather | `123456:ABC-DEF...` |
| `FILES_CHANNEL_ID` | Yes | Channel ID for file storage | `-1001234567890` |
| `LOGS_CHANNEL_ID` | Yes | Channel ID for logs | `-1001234567890` |
| `BACKUP_CHANNEL_LINK` | Yes | Backup channel invite link | `https://t.me/+ABC...` |
| `ADMIN_USER_IDS` | Yes | Admin user IDs (comma-separated) | `123456789,987654321` |

---

## Troubleshooting

### Bot not starting
- Check if BOT_TOKEN is correct
- Verify Python version (3.8+)
- Check logs for error messages

### Files not storing
- Ensure bot is admin in both channels
- Verify channel IDs are correct (negative numbers)
- Check bot has permission to post in channels

### Admin panel not showing
- Verify your user ID is in ADMIN_USER_IDS
- Get your ID from @userinfobot

### Cache issues
- Delete `file_cache.json` and restart bot
- Use "Rebuild Cache" in admin panel

---

## Monitoring

### Check bot status
```bash
# VPS
systemctl status filebot

# Docker
docker ps | grep filebot

# Heroku
heroku ps

# Railway/Render
Check dashboard
```

### View logs
```bash
# VPS
journalctl -u filebot -f

# Docker
docker logs -f filebot

# Heroku
heroku logs --tail
```

---

## Backup

### Important files to backup
- `file_cache.json` - File metadata
- `bot_messages.json` - Custom messages
- `.env` - Configuration (keep secure!)

### Backup command
```bash
tar -czf filebot-backup-$(date +%Y%m%d).tar.gz \
  file_cache.json bot_messages.json .env
```

---

## Security Best Practices

1. **Never commit sensitive data** to GitHub
2. **Use environment variables** for production
3. **Regularly update** dependencies
4. **Monitor logs** for suspicious activity
5. **Backup data** regularly
6. **Use HTTPS** for webhook mode (if applicable)

---

## Support

For deployment issues:
- Check logs first
- Review this guide
- Open an issue on GitHub
- Contact support

---

**Happy Deploying! 🚀**
