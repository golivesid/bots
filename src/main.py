import os
import sys
import logging
import json
import requests
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
        self.user_search_state = {}
    
    async def start(self, update: Update, context):
        """Handle the /start command"""
        user = update.effective_user
        
        # Refresh channels each time start is called
        self.channels = fetch_channels_from_github()
        
        try:
            # Check channel membership
            member = await context.bot.get_chat_member(REQUIRED_CHANNEL_ID, user.id)
            if member.status in ['member', 'administrator', 'creator']:
                await self.send_main_menu(update, context)
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

    async def send_main_menu(self, update: Update, context):
        """Send main menu with options"""
        keyboard = [
            [
                InlineKeyboardButton("📺 Channels", callback_data='show_channels'),
                InlineKeyboardButton("🔍 Search Channels", callback_data='search_channels')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 Welcome to TV Streaming Bot!\n"
            "Choose an option:", 
            reply_markup=reply_markup
        )

    async def send_channel_menu(self, update: Update, context):
        """Send available TV channels menu"""
        # Create keyboard dynamically based on fetched channels
        keyboard = []
        current_row = []
        for channel in sorted(self.channels.keys()):
            if len(current_row) == 3:  # 3 buttons per row
                keyboard.append(current_row)
                current_row = []
            current_row.append(InlineKeyboardButton(channel.upper(), callback_data=f'channel_{channel}'))
        
        # Add any remaining buttons
        if current_row:
            keyboard.append(current_row)
        
        # Add a back button
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
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
            # Get channel details
            channel_info = self.channels[channel]
            
            # Create inline keyboard for server selection
            keyboard = [
                [
                    InlineKeyboardButton("MPD Server", callback_data=f'server_mpd_{channel}'),
                    InlineKeyboardButton("M3U8 Server", callback_data=f'server_m3u8_{channel}')
                ],
                [InlineKeyboardButton("🔙 Back to Channels", callback_data='show_channels')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📺 {channel.upper()} Channel\n"
                "Select a streaming server:",
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("❌ Channel not found.")

    async def handle_server_selection(self, update: Update, context):
        """Handle server selection for a channel"""
        query = update.callback_query
        await query.answer()

        # Parse callback data
        _, server_type, channel = query.data.split('_')
        
        if channel in self.channels:
            channel_info = self.channels[channel]
            
            # Get appropriate stream based on server type
            if server_type == 'mpd':
                stream_link = channel_info.get('mpd', '')
                key_id = channel_info.get('mpd_key_id', '')
                key = channel_info.get('mpd_key', '')
            elif server_type == 'm3u8':
                stream_link = channel_info.get('m3u8', '')
                key_id = channel_info.get('m3u8_key_id', '')
                key = channel_info.get('m3u8_key', '')
            
            # Prepare video player HTML
            video_html = f"""
<html>
<head>
    <script src="https://content.jwplatform.com/libraries/SAHhwvZq.js"></script>
</head>
<body>
    <div id="jwplayerDiv"></div>
    <script>  
    jwplayer("jwplayerDiv").setup({{
        file: "{stream_link}",
        type: "{server_type}",
        drm: {{ "clearkey": {{
            "keyId": "{key_id}",
            "key": "{key}"
        }}}}
    }});
    </script>  
</body>
</html>
            """
            
            await query.edit_message_text(
                f"📺 Streaming {channel.upper()} Channel\n"
                f"Server: {server_type.upper()}\n"
                f"Link: {stream_link}\n\n"
                "Open the generated HTML in a browser to watch."
            )
            
            # Optionally, you could save the HTML to a file or send it as a document
            with open(f"{channel}_{server_type}_player.html", 'w') as f:
                f.write(video_html)
        else:
            await query.edit_message_text("❌ Channel not found.")

    async def start_channel_search(self, update: Update, context):
        """Initiate channel search process"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🔍 Search for a channel:\n"
            "Send me the channel name or partial name."
        )
        # Set search state for the user
        self.user_search_state[update.effective_user.id] = True

    async def handle_search_message(self, update: Update, context):
        """Handle channel search messages"""
        user_id = update.effective_user.id
        
        # Check if user is in search mode
        if user_id not in self.user_search_state or not self.user_search_state[user_id]:
            return
        
        # Get search query
        search_query = update.message.text.lower()
        
        # Find matching channels
        matching_channels = [
            channel for channel in self.channels.keys() 
            if search_query in channel.lower()
        ]
        
        if matching_channels:
            # Create keyboard with matching channels
            keyboard = [
                [InlineKeyboardButton(channel.upper(), callback_data=f'channel_{channel}') 
                 for channel in matching_channels]
            ]
            keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data='main_menu')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"🔍 Found {len(matching_channels)} matching channels:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "❌ No channels found matching your search."
            )
        
        # Reset search state
        self.user_search_state[user_id] = False

    async def handle_request_access(self, update: Update, context):
        """Handle access request callback"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "📝 Access Request Submitted\n"
            "An admin will review your request shortly."
        )

    async def handle_main_menu_callback(self, update: Update, context):
        """Handle main menu navigation"""
        query = update.callback_query
        await query.answer()

        if query.data == 'show_channels':
            await self.send_channel_menu(update, context)
        elif query.data == 'search_channels':
            await self.start_channel_search(update, context)

    def run(self):
        """Set up and run the bot"""
        logger.info(f"Initializing bot with token: {self.token[:4]}{'*' * (len(self.token) - 4)}")
        
        try:
            application = Application.builder().token(self.token).build()

            # Register handlers
            application.add_handler(CommandHandler("start", self.start))
            
            # Callback query handlers
            application.add_handler(CallbackQueryHandler(self.handle_main_menu_callback, pattern='^(show_channels|search_channels)$'))
            application.add_handler(CallbackQueryHandler(self.handle_channel_selection, pattern='^channel_'))
            application.add_handler(CallbackQueryHandler(self.handle_server_selection, pattern='^server_'))
            application.add_handler(CallbackQueryHandler(self.handle_request_access, pattern='^request_access$'))
            
            # Message handler for search
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_search_message))

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
