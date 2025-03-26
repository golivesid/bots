import os
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Replace with your actual bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# GitHub repository details for channels
GITHUB_REPO_OWNER = 'your_github_username'
GITHUB_REPO_NAME = 'tv-channels'
GITHUB_FILE_PATH = 'channels.json'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # Optional, for private repos

# Channel ID where users must join
REQUIRED_CHANNEL_ID = '@your_channel_username'

def fetch_channels_from_github():
    """
    Fetch TV channels from GitHub repository
    Supports both public and private repositories
    """
    # GitHub API URL for raw file content
    url = f'https://raw.githubusercontent.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/main/{GITHUB_FILE_PATH}'
    
    # Headers for authentication (if using private repo)
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    
    try:
        # Fetch the raw file content
        response = requests.get(url, headers=headers)
        
        # Raise an exception for bad responses
        response.raise_for_status()
        
        # Parse the JSON content
        channels = json.loads(response.text)
        return channels
    
    except requests.RequestException as e:
        print(f"Error fetching channels: {e}")
        return {}
    except json.JSONDecodeError:
        print("Invalid JSON format in channels file")
        return {}

class TelegramTVBot:
    def __init__(self, token):
        self.token = token
        self.channels = {}
    
    async def start(self, update: Update, context):
        """Handle the /start command"""
        user = update.effective_user
        
        # Refresh channels each time start is called (optional: you could cache)
        self.channels = fetch_channels_from_github()
        
        try:
            # Check channel membership
            member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user.id)
            if member.status in ['member', 'administrator', 'creator']:
                await self.send_channel_menu(update, context)
            else:
                await self.send_join_channel_message(update, context)
        except Exception:
            await self.send_join_channel_message(update, context)

    async def send_join_channel_message(self, update: Update, context):
        """Send message prompting user to join the channel"""
        keyboard = [
            [
                InlineKeyboardButton("Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL_ID.lstrip('@')}"),
                InlineKeyboardButton("Request Access", callback_data='request_access')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔒 You must join our channel to use this bot!\n"
            "Click 'Join Channel' to get access, or 'Request Access' if you need help.",
            reply_markup=reply_markup
        )

    async def send_channel_menu(self, update: Update, context):
        """Send available TV channels menu"""
        # Create keyboard dynamically based on fetched channels
        keyboard = [
            [InlineKeyboardButton(channel.upper(), callback_data=f'channel_{channel}') 
             for channel in self.channels.keys()]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 Select a TV Channel to Stream:", 
            reply_markup=reply_markup
        )

    async def handle_channel_selection(self, update: Update, context):
        """Handle channel selection callback"""
        query = update.callback_query
        await query.answer()

        # Extract selected channel
        channel = query.data.split('_')[1]
        
        if channel in self.channels:
            stream_link = self.channels[channel]
            await query.edit_message_text(
                f"📺 Streaming {channel.upper()} Channel\n"
                f"Link: {stream_link}"
            )
        else:
            await query.edit_message_text("❌ Channel not found.")

    async def handle_request_access(self, update: Update, context):
        """Handle access request callback"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "📝 Access Request Submitted\n"
            "An admin will review your request shortly."
        )

    def run(self):
        """Set up and run the bot"""
        application = Application.builder().token(self.token).build()

        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.handle_channel_selection, pattern='^channel_'))
        application.add_handler(CallbackQueryHandler(self.handle_request_access, pattern='^request_access$'))

        # Start the bot
        print("Bot is running...")
        application.run_polling(drop_pending_updates=True)

def main():
    bot = TelegramTVBot(BOT_TOKEN)
    bot.run()

if __name__ == '__main__':
    main()

# Example channels.json file to be hosted on GitHub
"""
{
    "cnn": "https://example.com/cnn_stream",
    "bbc": "https://example.com/bbc_stream",
    "espn": "https://example.com/espn_stream"
}
"""

# requirements.txt
"""
python-telegram-bot==20.7
requests==2.31.0
"""

# Dockerfile for Koyeb
"""
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
"""
