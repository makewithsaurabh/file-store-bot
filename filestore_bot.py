import os
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import hashlib
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
# Load from environment variables with fallback to hardcoded values

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8245683079:AAG7AYA7HsyKbo8VTUlBDDHYkMN_7m-t5WI")

# Channel IDs
FILES_CHANNEL_ID = int(os.getenv("FILES_CHANNEL_ID", "-1003403613314"))
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID", "-1003686127539"))

# Backup channel link
BACKUP_CHANNEL_LINK = os.getenv("BACKUP_CHANNEL_LINK", "https://t.me/+XV8UVRDn_91lZjk9")

# Admin user IDs (can add multiple admins)
# Support both comma-separated string from env and list
admin_ids_env = os.getenv("ADMIN_USER_IDS", "5948619751")
if isinstance(admin_ids_env, str):
    ADMIN_USER_IDS = [int(uid.strip()) for uid in admin_ids_env.split(",") if uid.strip()]
else:
    ADMIN_USER_IDS = [5948619751]

# Local cache file (optional, for faster lookups)
CACHE_FILE = 'file_cache.json'

# Messages configuration file
MESSAGES_FILE = 'bot_messages.json'


def is_admin(user_id):
    """Check if a user is an admin."""
    return user_id in ADMIN_USER_IDS

class MessageManager:
    """Manage custom bot messages"""
    def __init__(self):
        self.messages = self.load_messages()
    
    def load_messages(self):
        """Load messages from JSON file or create defaults"""
        if os.path.exists(MESSAGES_FILE):
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error("Messages file corrupted, using defaults")
                return self.get_default_messages()
        else:
            # Create default messages file
            defaults = self.get_default_messages()
            self.save_messages(defaults)
            return defaults
    
    def get_default_messages(self):
        """Get default bot messages"""
        return {
            "start_message": (
                "👋 *Welcome {user_name}!*\n\n"
                "🗄️ *File Storage Bot*\n\n"
                "I can help you store and share files easily using Telegram channels.\n\n"
                "*How it works:*\n"
                "📤 Send me any file (document, photo, video, audio)\n"
                "🔗 I'll store it in our database and generate a unique link\n"
                "📥 Anyone with the link can download the file\n"
                "💾 Files are stored permanently in our channels\n\n"
                "*Features:*\n"
                "✅ Unlimited file storage\n"
                "✅ Permanent shareable links\n"
                "✅ Download tracking\n"
                "✅ Easy file management\n\n"
                "Choose an option below or just send me a file! 📎"
            ),
            "help_message": (
                "ℹ️ *File Storage Bot - Help Guide*\n\n"
                "*📤 Uploading Files:*\n"
                "1. Send any file to the bot\n"
                "2. Wait for processing\n"
                "3. Get your unique share link\n"
                "4. File stored permanently!\n\n"
                "*🔗 Sharing Files:*\n"
                "1. Copy the share link\n"
                "2. Send to anyone\n"
                "3. They click and download\n"
                "4. Works anytime, anywhere!\n\n"
                "*📁 Managing Files:*\n"
                "• View all your uploads with /myfiles\n"
                "• Track download counts\n"
                "• Get file details anytime\n"
                "• Links never expire\n\n"
                "*Commands:*\n"
                "/start - Start the bot\n"
                "/myfiles - View your files\n"
                "/stats - View statistics\n"
                "/help - Show this help message\n"
                "/about - About this bot\n\n"
                "*✨ Features:*\n"
                "✅ Unlimited file storage\n"
                "✅ Permanent shareable links\n"
                "✅ Download tracking\n"
                "✅ Multiple file types\n"
                "✅ Fast and reliable"
            ),
            "about_message": (
                "ℹ️ *About File Storage Bot*\n\n"
                "🤖 *What is this bot?*\n"
                "This is a powerful file storage and sharing bot that uses Telegram's infrastructure to store and distribute files efficiently.\n\n"
                "*🎯 Purpose:*\n"
                "• Store files permanently in Telegram channels\n"
                "• Generate shareable links for easy distribution\n"
                "• Track downloads and manage your files\n"
                "• Provide a simple, reliable file sharing solution\n\n"
                "*⚙️ How it works:*\n"
                "When you send a file, it's stored in our secure Telegram channels and a unique link is generated. Anyone with the link can download the file anytime, anywhere.\n\n"
                "*✨ Key Features:*\n"
                "✅ Unlimited storage capacity\n"
                "✅ Permanent file links\n"
                "✅ Download statistics\n"
                "✅ Support for all file types\n"
                "✅ Fast and reliable delivery\n"
                "✅ Secure and private\n\n"
                "*📞 Support:*\n"
                "For help or questions, contact the bot administrator.\n\n"
                "*🔐 Privacy:*\n"
                "Your files are stored securely. Only users with the share link can access them.\n\n"
                "Thank you for using File Storage Bot! 🙏"
            )
        }
    
    def save_messages(self, messages=None):
        """Save messages to JSON file"""
        try:
            msgs = messages if messages else self.messages
            with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
                json.dump(msgs, f, indent=2, ensure_ascii=False)
            logger.info("Messages saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving messages: {e}")
            return False
    
    def get_message(self, message_type, **kwargs):
        """Get a message with variable replacement"""
        message = self.messages.get(message_type, "")
        
        # Replace variables
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            message = message.replace(placeholder, str(value))
        
        return message
    
    def update_message(self, message_type, new_content):
        """Update a specific message"""
        if message_type in self.messages:
            self.messages[message_type] = new_content
            return self.save_messages()
        return False
    
    def get_all_message_types(self):
        """Get list of all message types"""
        return list(self.messages.keys())

class FileStorage:
    """Channel-based storage - no local cache needed"""
    def __init__(self, bot_application=None):
        self.bot = None
        self.cache = {}  # Temporary in-memory cache for current session
        logger.info("FileStorage initialized - using channel-based storage")
    
    def set_bot(self, bot):
        """Set bot instance for channel operations"""
        self.bot = bot
    
    async def get_file_from_channel(self, unique_id):
        """Retrieve file metadata from logs channel by searching messages"""
        try:
            # Search through recent messages in logs channel
            async for message in self.bot.get_chat(LOGS_CHANNEL_ID).iter_history(limit=1000):
                if message.text and f"`{unique_id}`" in message.text:
                    # Extract JSON from message
                    if "```json" in message.text:
                        json_start = message.text.find("```json") + 7
                        json_end = message.text.find("```", json_start)
                        json_str = message.text[json_start:json_end].strip()
                        file_data = json.loads(json_str)
                        return file_data
            return None
        except Exception as e:
            logger.error(f"Error retrieving file from channel: {e}")
            return None
    
    async def add_to_cache(self, unique_id, file_data):
        """Add file data to memory cache (channel logging handled separately)"""
        self.cache[unique_id] = file_data
        logger.info(f"Added file {unique_id} to memory cache")
    
    def get_from_cache(self, unique_id):
        """Get file data from memory cache"""
        return self.cache.get(unique_id)
    
    async def update_downloads(self, unique_id):
        """Update download count - just increment in memory"""
        if unique_id in self.cache:
            self.cache[unique_id]['downloads'] = self.cache[unique_id].get('downloads', 0) + 1
            logger.info(f"Updated download count for {unique_id}")
    
    def get_user_files(self, user_id):
        """Get all files uploaded by a specific user from memory cache"""
        return [(uid, data) for uid, data in self.cache.items() if data.get('uploader_id') == user_id]
    
    def get_all_files(self):
        """Get all files in memory cache"""
        return list(self.cache.items())
    
    def get_total_downloads(self):
        """Get total downloads across all files in memory"""
        return sum(data.get('downloads', 0) for data in self.cache.values())


# Initialize storage
storage = FileStorage()

# Initialize message manager
message_manager = MessageManager()

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard based on user role"""
    if is_admin(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 My Files", callback_data="myfiles"),
             InlineKeyboardButton("📂 All Files", callback_data="allfiles")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats"),
             InlineKeyboardButton("🔄 Rebuild Cache", callback_data="rebuild")],
            [InlineKeyboardButton("✏️ Edit Messages", callback_data="editmessages")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help"),
             InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 My Files", callback_data="myfiles")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help"),
             InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    user_is_admin = is_admin(user_id)
    
    # Get custom start message with variable replacement
    welcome_text = message_manager.get_message(
        'start_message',
        user_name=user_name,
        user_id=user_id
    )
    
    if user_is_admin:
        welcome_text += "\n\n👑 *Admin Mode Active*"
    
    await update.message.reply_text(
        welcome_text, 
        parse_mode='Markdown', 
        reply_markup=get_main_menu_keyboard(user_id)
    )

async def store_file_in_channel(context, file_obj, file_type):
    """Store file in the files channel and return message ID"""
    try:
        if file_type == 'document':
            msg = await context.bot.send_document(
                chat_id=FILES_CHANNEL_ID,
                document=file_obj.file_id
            )
        elif file_type == 'photo':
            msg = await context.bot.send_photo(
                chat_id=FILES_CHANNEL_ID,
                photo=file_obj.file_id
            )
        elif file_type == 'video':
            msg = await context.bot.send_video(
                chat_id=FILES_CHANNEL_ID,
                video=file_obj.file_id
            )
        elif file_type == 'audio':
            msg = await context.bot.send_audio(
                chat_id=FILES_CHANNEL_ID,
                audio=file_obj.file_id
            )
        elif file_type == 'voice':
            msg = await context.bot.send_voice(
                chat_id=FILES_CHANNEL_ID,
                voice=file_obj.file_id
            )
        else:
            return None
        
        logger.info(f"Stored {file_type} file in channel, message_id: {msg.message_id}")
        return msg.message_id
    except Exception as e:
        logger.error(f"Error storing file in channel: {e}")
        return None

async def log_to_channel(context, log_data):
    """Log metadata and user activity to logs channel"""
    try:
        # Store complete metadata as JSON in the log for easy recovery
        metadata_json = json.dumps({
            'unique_id': log_data['unique_id'],
            'file_id': log_data['file_id'],
            'file_name': log_data['file_name'],
            'file_size_bytes': log_data.get('file_size_bytes'),
            'file_type': log_data['file_type'],
            'uploader_id': log_data['uploader_id'],
            'username': log_data.get('username'),
            'upload_date': log_data['upload_date'],
            'channel_message_id': log_data['channel_message_id']
        }, indent=2)
        
        log_text = (
            f"📊 *File Upload Log*\n\n"
            f"🆔 *Unique ID:* `{log_data['unique_id']}`\n"
            f"📄 *File Name:* `{log_data['file_name']}`\n"
            f"💾 *Size:* {log_data['file_size']}\n"
            f"👤 *Uploader ID:* `{log_data['uploader_id']}`\n"
            f"👤 *Username:* @{log_data.get('username', 'N/A')}\n"
            f"📅 *Date:* {log_data['upload_date']}\n"
            f"📍 *Channel Message ID:* {log_data['channel_message_id']}\n"
            f"🔗 *Share Link:* {log_data['share_link']}\n\n"
            f"```json\n{metadata_json}\n```"
        )
        await context.bot.send_message(
            chat_id=LOGS_CHANNEL_ID,
            text=log_text,
            parse_mode='Markdown'
        )
        logger.info(f"Logged file {log_data['unique_id']} to logs channel")
    except Exception as e:
        logger.error(f"Error logging to channel: {e}")

async def log_download_activity(context, file_id, file_name, downloader_user):
    """Log download activity with detailed user information"""
    try:
        download_log = {
            'file_id': file_id,
            'file_name': file_name,
            'downloader_id': downloader_user.id,
            'downloader_username': downloader_user.username,
            'downloader_first_name': downloader_user.first_name,
            'downloader_last_name': downloader_user.last_name,
            'download_timestamp': datetime.now().isoformat()
        }
        
        download_json = json.dumps(download_log, indent=2, ensure_ascii=False)
        
        log_text = (
            f"📥 *Download Activity*\n\n"
            f"🆔 *File ID:* `{file_id}`\n"
            f"📄 *File:* `{file_name}`\n\n"
            f"👤 *Downloader Info:*\n"
            f"├ *User ID:* `{downloader_user.id}`\n"
            f"├ *Username:* @{downloader_user.username or 'N/A'}\n"
            f"├ *Name:* {downloader_user.first_name} {downloader_user.last_name or ''}\n"
            f"└ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"```json\n{download_json}\n```"
        )
        
        await context.bot.send_message(
            chat_id=LOGS_CHANNEL_ID,
            text=log_text,
            parse_mode='Markdown'
        )
        logger.info(f"Logged download activity for file {file_id} by user {downloader_user.id}")
    except Exception as e:
        logger.error(f"Error logging download activity: {e}")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle received files and generate shareable links."""
    message = update.message
    user = message.from_user
    
    # Send processing message
    processing_msg = await message.reply_text("⏳ Processing your file... Please wait.")
    
    # Determine file type and get file object
    file_type = None
    if message.document:
        file = message.document
        file_name = file.file_name
        file_size = file.file_size
        file_type = 'document'
    elif message.photo:
        file = message.photo[-1]  # Get highest quality
        file_name = f"photo_{file.file_unique_id}.jpg"
        file_size = file.file_size
        file_type = 'photo'
    elif message.video:
        file = message.video
        file_name = file.file_name or f"video_{file.file_unique_id}.mp4"
        file_size = file.file_size
        file_type = 'video'
    elif message.audio:
        file = message.audio
        file_name = file.file_name or f"audio_{file.file_unique_id}.mp3"
        file_size = file.file_size
        file_type = 'audio'
    elif message.voice:
        file = message.voice
        file_name = f"voice_{file.file_unique_id}.ogg"
        file_size = file.file_size
        file_type = 'voice'
    else:
        await processing_msg.edit_text("❌ Unsupported file type!")
        return
    
    # Store file in channel
    channel_msg_id = await store_file_in_channel(context, file, file_type)
    
    if not channel_msg_id:
        await processing_msg.edit_text(
            "❌ *Error storing file*\n\n"
            "Please check:\n"
            "• Bot has admin rights in channels\n"
            "• Bot can post messages\n"
            "• Channel IDs are correct",
            parse_mode='Markdown'
        )
        return
    
    # Generate unique ID
    unique_id = hashlib.md5(f"{file.file_id}{datetime.now()}".encode()).hexdigest()[:8]
    
    # Get bot username for link generation
    bot = await context.bot.get_me()
    share_link = f"https://t.me/{bot.username}?start=file_{unique_id}"
    
    # Format file size
    size_mb = file_size / (1024 * 1024)
    size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB"
    
    # Prepare file data
    file_data = {
        'file_id': file.file_id,
        'file_name': file_name,
        'file_size': file_size,
        'file_size_bytes': file_size,  # Store raw bytes for logs
        'file_type': file_type,
        'uploader_id': user.id,
        'username': user.username,
        'upload_date': datetime.now().isoformat(),
        'channel_message_id': channel_msg_id,
        'downloads': 0,
        'share_link': share_link
    }
    
    # Add to local cache
    storage.add_to_cache(unique_id, file_data)
    
    # Log to channel
    log_data = file_data.copy()
    log_data['unique_id'] = unique_id
    log_data['file_size'] = size_str
    await log_to_channel(context, log_data)
    
    # Get file type emoji
    type_emoji = {
        'document': '📄',
        'photo': '🖼️',
        'video': '🎥',
        'audio': '🎵',
        'voice': '🎤'
    }.get(file_type, '📄')
    
    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton("📥 Download Now", callback_data=f"dl_{unique_id}")],
        [InlineKeyboardButton("🔗 Copy Share Link", url=share_link)],
        [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    response_text = (
        f"✅ *File Stored Successfully!*\n\n"
        f"{type_emoji} *File Details:*\n"
        f"├ *Name:* `{file_name}`\n"
        f"├ *Size:* {size_str}\n"
        f"├ *Type:* {file_type.title()}\n"
        f"└ *ID:* `{unique_id}`\n\n"
        f"📍 *Storage Info:*\n"
        f"├ Channel Message: {channel_msg_id}\n"
        f"└ Stored in database ✓\n\n"
        f"🔗 *Share Link:*\n`{share_link}`\n\n"
        f"💡 *Tip:* Click 'Copy Share Link' to open in browser and copy easily!"
    )
    
    await processing_msg.edit_text(response_text, parse_mode='Markdown', reply_markup=reply_markup)

async def send_file_to_user(context, chat_id, file_data, unique_id):
    """Helper function to send file to user based on type"""
    file_type = file_data.get('file_type', 'document')
    file_id = file_data['file_id']
    
    # Get file type emoji
    type_emoji = {
        'document': '📄',
        'photo': '🖼️',
        'video': '🎥',
        'audio': '🎵',
        'voice': '🎤'
    }.get(file_type, '📄')
    
    caption = f"{type_emoji} {file_data['file_name']}\n🆔 File ID: {unique_id}\n📥 Downloads: {file_data.get('downloads', 0)}"
    
    try:
        if file_type == 'document':
            await context.bot.send_document(chat_id=chat_id, document=file_id, caption=caption)
        elif file_type == 'photo':
            await context.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption)
        elif file_type == 'video':
            await context.bot.send_video(chat_id=chat_id, video=file_id, caption=caption)
        elif file_type == 'audio':
            await context.bot.send_audio(chat_id=chat_id, audio=file_id, caption=caption)
        elif file_type == 'voice':
            await context.bot.send_voice(chat_id=chat_id, voice=file_id)
        
        logger.info(f"Sent file {unique_id} to user {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        return False

async def handle_start_parameter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with file parameter."""
    if not context.args:
        await start(update, context)
        return
    
    param = context.args[0]
    if param.startswith('file_'):
        unique_id = param.replace('file_', '')
        user_id = update.effective_user.id
        
        # Check if file exists
        file_data = storage.get_from_cache(unique_id)
        
        if not file_data:
            await update.message.reply_text(
                "❌ *File Not Found*\n\n"
                "This file may have been deleted or the link is incorrect.",
                parse_mode='Markdown'
            )
            return
        
        # For non-admins: show join channel prompt
        if not is_admin(user_id):
            keyboard = [
                [InlineKeyboardButton("📥 Get File", callback_data=f"get_{unique_id}")],
                [InlineKeyboardButton("📢 Join Our Channel", url=BACKUP_CHANNEL_LINK)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get file info
            size_mb = file_data.get('file_size', 0) / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_data.get('file_size', 0) / 1024:.2f} KB"
            
            type_emoji = {
                'document': '📄',
                'photo': '🖼️',
                'video': '🎥',
                'audio': '🎵',
                'voice': '🎤'
            }.get(file_data.get('file_type', 'document'), '📄')
            
            await update.message.reply_text(
                f"🔒 *File Ready for Download*\n\n"
                f"{type_emoji} *File Details:*\n"
                f"├ *Name:* `{file_data['file_name']}`\n"
                f"├ *Size:* {size_str}\n"
                f"├ *Type:* {file_data.get('file_type', 'document').title()}\n"
                f"└ *Downloads:* {file_data.get('downloads', 0)}\n\n"
                f"👇 Click below to get your file!\n\n"
                f"💡 *Support us by joining our backup channel!*",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return
        
        # Admin: direct access
        success = await send_file_to_user(context, update.effective_chat.id, file_data, unique_id)
        
        if success:
            await storage.update_downloads(unique_id)
            
            # Log download activity with detailed user info
            await log_download_activity(context, unique_id, file_data['file_name'], update.effective_user)
        else:
            await update.message.reply_text("❌ Error retrieving file. Please try again.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Back/Cancel - Delete message for clean UI
    if data in ["back", "cancel"]:
        try:
            await query.message.delete()
        except:
            await query.message.edit_text("✅ Cancelled", reply_markup=None)
        return
    
    # Main Menu
    if data == "menu":
        user_name = query.from_user.first_name
        welcome_text = (
            f"👋 *Welcome back, {user_name}!*\n\n"
            "🗄️ *File Storage Bot - Main Menu*\n\n"
            "Choose an option below:"
        )
        
        await query.edit_message_text(
            welcome_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard(user_id)
        )
        return
    
    # My Files
    if data == "myfiles":
        user_files = storage.get_user_files(user_id)
        
        if not user_files:
            await query.edit_message_text(
                "📭 *No Files Yet*\n\n"
                "You haven't uploaded any files.\n\n"
                "💡 Send me a file to get started!",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
            )
            return
        
        bot = await context.bot.get_me()
        response = "📁 *Your Uploaded Files*\n\n"
        
        for uid, d in user_files[-15:]:  # Show last 15 files
            file_size = d.get('file_size', 0)
            size_mb = file_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB"
            
            share_link = f"https://t.me/{bot.username}?start=file_{uid}"
            
            type_emoji = {
                'document': '📄',
                'photo': '🖼️',
                'video': '🎥',
                'audio': '🎵',
                'voice': '🎤'
            }.get(d.get('file_type', 'document'), '📄')
            
            # Truncate long filenames
            display_name = d['file_name'][:40] + "..." if len(d['file_name']) > 40 else d['file_name']
            
            response += (
                f"{type_emoji} *{display_name}*\n"
                f"├ 🆔 ID: `{uid}`\n"
                f"├ 💾 Size: {size_str}\n"
                f"├ 📥 Downloads: {d.get('downloads', 0)}\n"
                f"├ 📅 Date: {d['upload_date'][:10]}\n"
                f"└ 🔗 [Share Link]({share_link})\n\n"
            )
        
        if len(user_files) > 15:
            response += f"_Showing last 15 of {len(user_files)} total files_\n\n"
        
        response += f"📊 *Total Files:* {len(user_files)}"
        
        await query.edit_message_text(
            response,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
        )
        return
    
    # All Files (Admin Only)
    if data == "allfiles":
        if not is_admin(user_id):
            await query.answer("❌ Admin access required!", show_alert=True)
            return
        
        all_files = storage.get_all_files()
        
        if not all_files:
            await query.edit_message_text(
                "📭 *No Files in System*\n\n"
                "No files have been uploaded yet.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
            )
            return
        
        bot = await context.bot.get_me()
        response = "📂 *All Files in System*\n\n"
        
        for uid, d in all_files[-15:]:  # Show last 15 files
            file_size = d.get('file_size', 0)
            size_mb = file_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB"
            
            share_link = f"https://t.me/{bot.username}?start=file_{uid}"
            
            type_emoji = {
                'document': '📄',
                'photo': '🖼️',
                'video': '🎥',
                'audio': '🎵',
                'voice': '🎤'
            }.get(d.get('file_type', 'document'), '📄')
            
            display_name = d['file_name'][:35] + "..." if len(d['file_name']) > 35 else d['file_name']
            
            response += (
                f"{type_emoji} *{display_name}*\n"
                f"├ 🆔 ID: `{uid}`\n"
                f"├ 👤 By: @{d.get('username', 'Unknown')} (`{d.get('uploader_id', 'N/A')}`)\n"
                f"├ 💾 Size: {size_str}\n"
                f"├ 📥 Downloads: {d.get('downloads', 0)}\n"
                f"├ 📅 Date: {d['upload_date'][:10]}\n"
                f"└ 🔗 [Link]({share_link})\n\n"
            )
        
        if len(all_files) > 15:
            response += f"_Showing last 15 of {len(all_files)} total files_\n\n"
        
        response += f"📊 *Total Files:* {len(all_files)}"
        
        await query.edit_message_text(
            response,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
        )
        return
    
    # Statistics
    if data == "stats":
        total_files = len(storage.cache)
        total_downloads = storage.get_total_downloads()
        
        if is_admin(user_id):
            # Admin statistics
            response = (
                f"📊 *Bot Statistics (Admin View)*\n\n"
                f"*Global Stats:*\n"
                f"├ 📁 Total Files: {total_files}\n"
                f"├ 📥 Total Downloads: {total_downloads}\n"
                f"└ 👥 Total Users: {len(set(d.get('uploader_id') for d in storage.cache.values()))}\n\n"
                f"*Storage Info:*\n"
                f"├ 🗄️ Files Channel: `{FILES_CHANNEL_ID}`\n"
                f"├ 📝 Logs Channel: `{LOGS_CHANNEL_ID}`\n"
                f"└ 💾 Cache Entries: {len(storage.cache)}\n\n"
                f"*Average Stats:*\n"
                f"├ Avg Downloads/File: {total_downloads/total_files if total_files > 0 else 0:.1f}\n"
                f"└ Cache Status: {'✅ Healthy' if len(storage.cache) > 0 else '⚠️ Empty'}"
            )
        else:
            # User statistics - only show personal stats
            user_files = storage.get_user_files(user_id)
            user_downloads = sum(d.get('downloads', 0) for _, d in user_files)
            
            response = (
                f"📊 *Your Statistics*\n\n"
                f"*Your Activity:*\n"
                f"├ 📁 Files Uploaded: {len(user_files)}\n"
                f"├ 📥 Total Downloads: {user_downloads}\n"
                f"└ 📈 Avg Downloads/File: {user_downloads/len(user_files) if len(user_files) > 0 else 0:.1f}\n\n"
                f"💡 *Tip:* Upload more files to track your sharing activity!"
            )
        
        await query.edit_message_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
        )
        return
    
    # Help
    if data == "help":
        help_text = message_manager.get_message('help_message')
        
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
        )
        return
    
    # About
    if data == "about":
        about_text = message_manager.get_message('about_message')
        
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
        )
        return
    
    # Edit Messages (Admin Only)
    if data == "editmessages":
        if not is_admin(user_id):
            await query.answer("❌ Admin access required!", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("📝 Edit Start Message", callback_data="edit_start_message")],
            [InlineKeyboardButton("📝 Edit Help Message", callback_data="edit_help_message")],
            [InlineKeyboardButton("📝 Edit About Message", callback_data="edit_about_message")],
            [InlineKeyboardButton("« Back to Menu", callback_data="menu")]
        ]
        
        await query.edit_message_text(
            "✏️ *Edit Bot Messages*\n\n"
            "Select which message you want to edit:\n\n"
            "*Available Variables:*\n"
            "• `{user_name}` - User's first name\n"
            "• `{user_id}` - User's ID\n\n"
            "*Note:* Messages support Markdown formatting.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Edit specific message types
    if data.startswith('edit_'):
        if not is_admin(user_id):
            await query.answer("❌ Admin access required!", show_alert=True)
            return
        
        message_type = data.replace('edit_', '')
        
        # Store editing state in context
        context.user_data['editing_message'] = message_type
        
        # Get current message
        current_msg = message_manager.messages.get(message_type, "")
        
        # Truncate if too long for display
        display_msg = current_msg[:500] + "..." if len(current_msg) > 500 else current_msg
        
        message_names = {
            'start_message': 'Start Message',
            'help_message': 'Help Message',
            'about_message': 'About Message'
        }
        
        await query.edit_message_text(
            f"✏️ *Editing {message_names.get(message_type, 'Message')}*\n\n"
            f"*Current Message:*\n"
            f"```\n{display_msg}\n```\n\n"
            f"📝 Send me the new message text.\n\n"
            f"*Available Variables:*\n"
            f"• `{{user_name}}` - User's first name\n"
            f"• `{{user_id}}` - User's ID\n\n"
            f"Use /cancel to cancel editing.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Cancel", callback_data="editmessages")]])
        )
        return
    
    # Preview edited message
    if data.startswith('preview_'):
        if not is_admin(user_id):
            await query.answer("❌ Admin access required!", show_alert=True)
            return
        
        message_type = data.replace('preview_', '')
        preview_text = context.user_data.get('preview_text', '')
        
        # Show preview with variables replaced
        preview_display = message_manager.get_message(
            message_type,
            user_name=query.from_user.first_name,
            user_id=user_id
        ) if message_type in message_manager.messages else preview_text
        
        keyboard = [
            [InlineKeyboardButton("✅ Save", callback_data=f"save_{message_type}"),
             InlineKeyboardButton("❌ Cancel", callback_data="editmessages")]
        ]
        
        await query.edit_message_text(
            f"👁️ *Preview*\n\n{preview_display}\n\n"
            f"Save this message?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Save edited message
    if data.startswith('save_'):
        if not is_admin(user_id):
            await query.answer("❌ Admin access required!", show_alert=True)
            return
        
        message_type = data.replace('save_', '')
        new_content = context.user_data.get('new_message_content', '')
        
        if new_content:
            success = message_manager.update_message(message_type, new_content)
            
            if success:
                # Clear editing state
                context.user_data.pop('editing_message', None)
                context.user_data.pop('new_message_content', None)
                context.user_data.pop('preview_text', None)
                
                await query.edit_message_text(
                    "✅ *Message Updated Successfully!*\n\n"
                    "The new message has been saved and will be used immediately.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
                )
            else:
                await query.edit_message_text(
                    "❌ *Error Saving Message*\n\n"
                    "There was an error saving the message. Please try again.",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data="editmessages")]])
                )
        return
    
    # Rebuild Cache (Admin Only)
    if data == "rebuild":
        if not is_admin(user_id):
            await query.answer("❌ Admin access required!", show_alert=True)
            return
        
        await query.edit_message_text(
            "🔄 *Cache Rebuild*\n\n"
            "Current cache status:\n"
            f"├ 📊 Files in cache: {len(storage.cache)}\n"
            f"├ 💾 Cache file: `{CACHE_FILE}`\n"
            f"└ ✅ Status: Operational\n\n"
            "*About Cache:*\n"
            "The cache stores file metadata locally for fast access. "
            "All data is also logged in the Logs Channel for permanent backup.\n\n"
            "*Recovery:*\n"
            "If cache is lost, files are automatically recovered from the Logs Channel "
            "when accessed via their share links.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="menu")]])
        )
        return
    
    # Get File (with join prompt)
    if data.startswith('get_'):
        unique_id = data.replace('get_', '')
        
        file_data = storage.get_from_cache(unique_id)
        
        if not file_data:
            await query.edit_message_text(
                "❌ *File Not Found*\n\n"
                "This file may have been deleted or the link is incorrect.",
                parse_mode='Markdown'
            )
            return
        
        # Send file to user
        success = await send_file_to_user(context, query.message.chat_id, file_data, unique_id)
        
        if success:
            await storage.update_downloads(unique_id)
            
            # Show join channel button after sending
            keyboard = [
                [InlineKeyboardButton("📢 Join Our Backup Channel", url=BACKUP_CHANNEL_LINK)],
                [InlineKeyboardButton("✅ Done", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "✅ *File Sent Successfully!*\n\n"
                "Your file has been sent to this chat.\n\n"
                "💡 *Support us by joining our backup channel!*\n"
                "Get updates, exclusive content, and more files.",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Log download activity with detailed user info
            await log_download_activity(context, unique_id, file_data['file_name'], query.from_user)
        else:
            await query.edit_message_text(
                "❌ *Error Sending File*\n\n"
                "There was an error retrieving your file. Please try again later.",
                parse_mode='Markdown'
            )
        return
    
    # Download File (from file upload message)
    if data.startswith('dl_'):
        unique_id = data.replace('dl_', '')
        file_data = storage.get_from_cache(unique_id)
        
        if not file_data:
            await query.answer("❌ File not found!", show_alert=True)
            return
        
        success = await send_file_to_user(context, query.message.chat_id, file_data, unique_id)
        
        if success:
            await storage.update_downloads(unique_id)
            await query.answer("✅ File sent successfully!", show_alert=False)
            
            # Log download activity with detailed user info
            await log_download_activity(context, unique_id, file_data['file_name'], query.from_user)
        else:
            await query.answer("❌ Error sending file. Please try again.", show_alert=True)
        return

# ===== COMMAND HANDLERS =====

async def my_files_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command version of my files with detailed view"""
    user_id = update.message.from_user.id
    user_files = storage.get_user_files(user_id)
    
    if not user_files:
        await update.message.reply_text(
            "📭 *No Files Yet*\n\n"
            "You haven't uploaded any files.\n\n"
            "💡 Send me a file to get started!",
            parse_mode='Markdown'
        )
        return
    
    bot = await context.bot.get_me()
    response = "📁 *Your Uploaded Files*\n\n"
    
    for uid, d in user_files[-15:]:
        file_size = d.get('file_size', 0)
        size_mb = file_size / (1024 * 1024)
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_size / 1024:.2f} KB"
        
        share_link = f"https://t.me/{bot.username}?start=file_{uid}"
        
        type_emoji = {
            'document': '📄',
            'photo': '🖼️',
            'video': '🎥',
            'audio': '🎵',
            'voice': '🎤'
        }.get(d.get('file_type', 'document'), '📄')
        
        display_name = d['file_name'][:40] + "..." if len(d['file_name']) > 40 else d['file_name']
        
        response += (
            f"{type_emoji} *{display_name}*\n"
            f"├ 🆔 ID: `{uid}`\n"
            f"├ 💾 Size: {size_str}\n"
            f"├ 📥 Downloads: {d.get('downloads', 0)}\n"
            f"├ 📅 Date: {d['upload_date'][:10]}\n"
            f"└ 🔗 [Share Link]({share_link})\n\n"
        )
    
    if len(user_files) > 15:
        response += f"_Showing last 15 of {len(user_files)} total files_\n\n"
    
    response += f"📊 *Total Files:* {len(user_files)}"
    
    await update.message.reply_text(
        response,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command version of statistics"""
    user_id = update.message.from_user.id
    total_files = len(storage.cache)
    total_downloads = storage.get_total_downloads()
    
    if is_admin(user_id):
        # Admin statistics
        response = (
            f"📊 *Bot Statistics (Admin View)*\n\n"
            f"*Global Stats:*\n"
            f"├ 📁 Total Files: {total_files}\n"
            f"├ 📥 Total Downloads: {total_downloads}\n"
            f"└ 👥 Total Users: {len(set(d.get('uploader_id') for d in storage.cache.values()))}\n\n"
            f"*Storage Info:*\n"
            f"├ 🗄️ Files Channel: `{FILES_CHANNEL_ID}`\n"
            f"├ 📝 Logs Channel: `{LOGS_CHANNEL_ID}`\n"
            f"└ 💾 Cache Entries: {len(storage.cache)}\n\n"
            f"*Average Stats:*\n"
            f"├ Avg Downloads/File: {total_downloads/total_files if total_files > 0 else 0:.1f}\n"
            f"└ Cache Status: {'✅ Healthy' if len(storage.cache) > 0 else '⚠️ Empty'}"
        )
    else:
        # User statistics - only show personal stats
        user_files = storage.get_user_files(user_id)
        user_downloads = sum(d.get('downloads', 0) for _, d in user_files)
        
        response = (
            f"📊 *Your Statistics*\n\n"
            f"*Your Activity:*\n"
            f"├ 📁 Files Uploaded: {len(user_files)}\n"
            f"├ 📥 Total Downloads: {user_downloads}\n"
            f"└ 📈 Avg Downloads/File: {user_downloads/len(user_files) if len(user_files) > 0 else 0:.1f}\n\n"
            f"💡 *Tip:* Upload more files to track your sharing activity!"
        )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command version of help"""
    help_text = message_manager.get_message('help_message')
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show about message"""
    about_text = message_manager.get_message('about_message')
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any ongoing editing operation"""
    user_id = update.message.from_user.id
    
    if not is_admin(user_id):
        return
    
    # Clear editing state
    if 'editing_message' in context.user_data:
        context.user_data.pop('editing_message', None)
        context.user_data.pop('new_message_content', None)
        context.user_data.pop('preview_text', None)
        
        await update.message.reply_text(
            "✅ Editing cancelled.",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    else:
        await update.message.reply_text("No active editing session.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for message editing"""
    user_id = update.message.from_user.id
    
    # Check if admin is editing a message
    if is_admin(user_id) and 'editing_message' in context.user_data:
        message_type = context.user_data['editing_message']
        new_content = update.message.text
        
        # Store the new content
        context.user_data['new_message_content'] = new_content
        context.user_data['preview_text'] = new_content
        
        # Temporarily update message for preview
        old_content = message_manager.messages.get(message_type, '')
        message_manager.messages[message_type] = new_content
        
        # Show preview with variables replaced
        preview_display = message_manager.get_message(
            message_type,
            user_name=update.message.from_user.first_name,
            user_id=user_id
        )
        
        # Restore old content (don't save yet)
        message_manager.messages[message_type] = old_content
        
        keyboard = [
            [InlineKeyboardButton("✅ Save", callback_data=f"save_{message_type}"),
             InlineKeyboardButton("❌ Cancel", callback_data="editmessages")]
        ]
        
        message_names = {
            'start_message': 'Start Message',
            'help_message': 'Help Message',
            'about_message': 'About Message'
        }
        
        await update.message.reply_text(
            f"👁️ *Preview of {message_names.get(message_type, 'Message')}*\n\n"
            f"{preview_display}\n\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"Save this message?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def post_init(application: Application):
    """Set up bot commands after initialization"""
    from telegram import BotCommand
    
    commands = [
        BotCommand("start", "Start the bot and see menu"),
        BotCommand("myfiles", "View your uploaded files"),
        BotCommand("stats", "View bot statistics"),
        BotCommand("help", "Show help guide"),
        BotCommand("about", "About this bot"),
        BotCommand("cancel", "Cancel current operation"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands configured successfully!")

def main():
    """Start the bot."""
    logger.info("Starting File Storage Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", handle_start_parameter))
    application.add_handler(CommandHandler("myfiles", my_files_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    
    # Add text message handler for editing messages (must be before file handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Add file handler for all file types
    application.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO | filters.VOICE,
        handle_file
    ))
    
    # Add callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("=" * 50)
    logger.info("Bot started successfully!")
    logger.info(f"Files Channel ID: {FILES_CHANNEL_ID}")
    logger.info(f"Logs Channel ID: {LOGS_CHANNEL_ID}")
    logger.info(f"Admin User IDs: {ADMIN_USER_IDS}")
    logger.info(f"Cache File: {CACHE_FILE}")
    logger.info("=" * 50)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
