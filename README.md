# 📁 Telegram File Storage Bot

A powerful Telegram bot for storing and sharing files using Telegram channels as a backend. Features include unlimited file storage, permanent shareable links, download tracking, and an admin panel with customizable messages.

## ✨ Features

- **Unlimited File Storage**: Store documents, photos, videos, audio files, and voice messages
- **Permanent Shareable Links**: Generate unique links for each file that never expire
- **Download Tracking**: Monitor how many times each file has been downloaded
- **Admin Panel**: Comprehensive admin controls including:
  - View all files in the system
  - Edit bot messages (start, help, about)
  - View statistics and analytics
  - Rebuild cache functionality
- **Customizable Messages**: Admins can customize all bot messages through the bot interface
- **Force Join**: Optional channel join requirement for file access
- **Multi-file Support**: Supports all Telegram file types

## 📋 Requirements

- Python 3.8 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Two Telegram channels (one for files, one for logs)
- Channel admin rights for the bot

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/file-store-bot.git
cd file-store-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the Bot

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your configuration:

```env
BOT_TOKEN=your_bot_token_here
FILES_CHANNEL_ID=-1001234567890
LOGS_CHANNEL_ID=-1001234567890
BACKUP_CHANNEL_LINK=https://t.me/your_channel
ADMIN_USER_IDS=123456789,987654321
```

**Or** edit `filestore_bot.py` directly and update these variables:

```python
BOT_TOKEN = "your_bot_token_here"
FILES_CHANNEL_ID = -1001234567890  # Your files channel ID
LOGS_CHANNEL_ID = -1001234567890   # Your logs channel ID
BACKUP_CHANNEL_LINK = "https://t.me/your_channel"
ADMIN_USER_IDS = [123456789]  # Your Telegram user ID
```

### 4. Set Up Telegram Channels

1. Create two private channels (one for files, one for logs)
2. Add your bot as an admin to both channels
3. Get the channel IDs:
   - Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
   - Use the channel ID (it will be negative, like `-1001234567890`)

### 5. Run the Bot

```bash
python filestore_bot.py
```

## 📖 Usage

### For Users

1. **Upload Files**: Send any file to the bot
2. **Get Share Link**: Bot generates a permanent shareable link
3. **Share**: Send the link to anyone
4. **Download**: Recipients click the link to download

### For Admins

- `/start` - Access admin panel
- `/myfiles` - View your uploaded files
- `/stats` - View bot statistics
- `/help` - Show help guide
- `/about` - About the bot
- **Edit Messages** - Customize bot messages through the admin panel

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Your Telegram bot token | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `FILES_CHANNEL_ID` | Channel ID for storing files | `-1001234567890` |
| `LOGS_CHANNEL_ID` | Channel ID for logs | `-1001234567890` |
| `BACKUP_CHANNEL_LINK` | Invite link to backup channel | `https://t.me/+ABC123xyz` |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | `123456789,987654321` |

### Getting Your User ID

Send `/start` to [@userinfobot](https://t.me/userinfobot) to get your Telegram user ID.

## 📁 File Structure

```
file-store-bot/
├── filestore_bot.py       # Main bot script
├── bot_messages.json      # Customizable bot messages
├── file_cache.json        # Local cache (auto-generated)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🐳 Docker Deployment (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "filestore_bot.py"]
```

Build and run:

```bash
docker build -t file-store-bot .
docker run -d --name file-store-bot --env-file .env file-store-bot
```

## 🌐 Deployment Options

### VPS/Server

1. Clone the repository on your server
2. Install dependencies
3. Configure the bot
4. Run with `screen` or `tmux`:
   ```bash
   screen -S filebot
   python filestore_bot.py
   ```
5. Detach with `Ctrl+A, D`

### Heroku

1. Create a new Heroku app
2. Add a `Procfile`:
   ```
   worker: python filestore_bot.py
   ```
3. Set environment variables in Heroku dashboard
4. Deploy via Git

### Railway/Render

1. Connect your GitHub repository
2. Set environment variables
3. Deploy automatically

## 🔒 Security Notes

- **Never commit** your `.env` file or bot token to GitHub
- Keep your `file_cache.json` private (contains file metadata)
- Only share admin access with trusted users
- Regularly monitor the logs channel for suspicious activity

## 🛠️ Customization

### Editing Bot Messages

Admins can edit messages directly through the bot:

1. Send `/start` to the bot
2. Click "Edit Messages"
3. Select the message to edit
4. Send new message text
5. Preview and save

### Supported Variables in Messages

- `{user_name}` - User's first name
- `{user_id}` - User's Telegram ID

## 📊 Features Breakdown

### File Management
- Upload any file type
- Automatic file storage in channels
- Unique ID generation for each file
- Download counter

### Admin Features
- View all files in system
- Edit bot messages
- Statistics dashboard
- Cache management

### User Features
- View personal uploaded files
- Track download statistics
- Permanent shareable links

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 💬 Support

For issues and questions:
- Open an issue on GitHub
- Contact the bot administrator

## 🙏 Acknowledgments

- Built with [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Inspired by the need for simple file sharing solutions

---

**Made with ❤️ for the Telegram community**
