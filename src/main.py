import os
import sys
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

def get_bot_token():
    """
    Retrieve bot token from environment variables with robust error handling
    """
    token = os.getenv('8063753854:AAE4mAxHO1X4xV0X_l334rS_rZJ_NWQz3VU')
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Please set the Telegram Bot Token obtained from @BotFather")
        sys.exit(1)
    return token

# GitHub repository details for channels
GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER', 'seeubot')
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME', 'bots')
GITHUB_FILE_PATH = os.getenv('GITHUB_FILE_PATH', 'channels.json')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # Optional, for private repos

# Channel ID where users must join
REQUIRED_CHANNEL_ID = os.getenv('REQUIRED_CHANNEL_ID', '@your_channel_username')

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
        # Add debug print to verify token is not empty
        print(f"Using bot token: {self.token[:4]}{'*' * (len(self.token) - 4)}")
        
        application = Application.builder().token(self.token).build()

        # Register handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.handle_channel_selection, pattern='^channel_'))
        application.add_handler(CallbackQueryHandler(self.handle_request_access, pattern='^request_access$'))

        # Start the bot
        print("Bot is running...")
        application.run_polling(drop_pending_updates=True)

def main():
    # Get the bot token
    bot_token = get_bot_token()
    
    # Create and run the bot
    bot = TelegramTVBot(bot_token)
    bot.run()

if __name__ == '__main__':
    main()




import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

def get_bot_token():
    """
    Retrieve bot token from environment variables with robust error handling
    """
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Please set the Telegram Bot Token obtained from @BotFather")
        sys.exit(1)
    return token

# GitHub repository details for channels
GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER', 'your_github_username')
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME', 'tv-channels')
GITHUB_FILE_PATH = os.getenv('GITHUB_FILE_PATH', 'channels.json')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # Optional, for private repos

# Channel ID where users must join
REQUIRED_CHANNEL_ID = os.getenv('REQUIRED_CHANNEL_ID', '@your_channel_username')

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
        logger.info(f"Fetching channels from: {url}")
        response = requests.get(url, headers=headers)
        
        # Raise an exception for bad responses
        response.raise_for_status()
        
        # Parse the JSON content
        channels = json.loads(response.text)
        logger.info(f"Successfully fetched {len(channels)} channels")
        return channels
    
    except requests.RequestException as e:
        logger.error(f"Error fetching channels: {e}")
        return {}
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in channels file")
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
        except Exception as e:
            logger.error(f"Error in start command: {e}")
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
        # Add debug print to verify token is not empty
        logger.info(f"Initializing bot with token: {self.token[:4]}{'*' * (len(self.token) - 4)}")
        
        try:
            application = Application.builder().token(self.token).build()

            # Register handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CallbackQueryHandler(self.handle_channel_selection, pattern='^channel_'))
            application.add_handler(CallbackQueryHandler(self.handle_request_access, pattern='^request_access$'))

            # Start the bot
            logger.info("Bot is running...")
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Fatal error in bot execution: {e}")
            sys.exit(1)

def main():
    try:
        # Get the bot token
        bot_token = get_bot_token()
        
        # Create and run the bot
        bot = TelegramTVBot(bot_token)
        bot.run()
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
