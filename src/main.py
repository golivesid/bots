import logging
import json
import os
import uuid
from typing import List, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
MAX_SEARCH_RESULTS = 10

class ChannelStreamBot:
    def __init__(self, token: str):
        self.token = token
        self.channels = self.load_channels()
        self.generate_player_pages()

    def load_channels(self) -> List[Dict]:
        """Load channels from JSON file with error handling"""
        try:
            with open('channels.json', 'r', encoding='utf-8') as file:
                return json.load(file).get('channels', [])
        except FileNotFoundError:
            logger.error("Channels JSON file not found!")
            return []
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in channels file")
            return []

    def generate_player_pages(self):
        """Generate individual HTML player pages for each channel"""
        # Create players directory if it doesn't exist
        os.makedirs('players', exist_ok=True)

        for channel in self.channels:
            player_html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>{channel['name']} - Stream Player</title>
    <script src="https://content.jwplatform.com/libraries/SAHhwvZq.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #player {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="player"></div>
    <script>
        jwplayer("player").setup({{
            sources: [
                {{
                    file: "{channel['url']}",
                    type: "hls"
                }},
                {{
                    file: "{channel['dash_url']}",
                    type: "dash",
                    drm: {{
                        "clearkey": {{
                            "keyId": "{channel['drm']['clearkey']['keyId']}",
                            "key": "{channel['drm']['clearkey']['key']}"
                        }}
                    }}
                }}
            ],
            width: "100%",
            height: "100%",
            autostart: true,
            controls: true
        }});
    </script>
</body>
</html>
            '''
            
            # Generate unique filename based on channel name
            filename = f"players/{channel['name'].lower().replace(' ', '_')}_player.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(player_html)

    def search_channels(self, query: str) -> List[Dict]:
        """Search channels by name, description, or category"""
        query = query.lower()
        return [
            channel for channel in self.channels
            if (query in channel['name'].lower() or 
                query in channel.get('description', '').lower() or 
                any(query in cat.lower() for cat in channel.get('category', [])))
        ][:MAX_SEARCH_RESULTS]

    def create_channel_keyboard(self, channels: List[Dict]):
        """Create inline keyboard for channel results"""
        keyboard = [
            [InlineKeyboardButton(
                text=f"📺 {channel['name']}", 
                callback_data=f"channel_{self.channels.index(channel)}"
            )] for channel in channels
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 Welcome to the Channel Stream Bot!

Commands:
• /search [keyword] - Find channels
• /start - Show this message
• /help - Get assistance
        """
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
📖 Channel Stream Bot Help

Search Tips:
- Use /search with keywords
- Search by channel name, description, or category
- Click a channel to watch live stream

Example searches:
/search sports
/search news
/search movies
        """
        await update.message.reply_text(help_message)

    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel search"""
        try:
            query = context.args[0] if context.args else None
            
            if not query:
                await update.message.reply_text("Please provide a search term. Usage: /search keyword")
                return

            results = self.search_channels(query)
            
            if not results:
                await update.message.reply_text(f"No channels found matching '{query}'.")
                return
            
            keyboard = self.create_channel_keyboard(results)
            await update.message.reply_text(
                f"Found {len(results)} channels matching '{query}':", 
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text("An error occurred during search.")

    async def channel_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel selection callback"""
        query = update.callback_query
        await query.answer()

        try:
            channel_index = int(query.data.split('_')[1])
            selected_channel = self.channels[channel_index]
            
            # Generate a unique player URL
            player_url = f"players/{selected_channel['name'].lower().replace(' ', '_')}_player.html"
            
            stream_info = f"""
📺 Channel: {selected_channel['name']}

Click the link below to watch the stream:
{player_url}

Stream Links:
HLS: {selected_channel['url']}
DASH: {selected_channel['dash_url']}
            """
            
            await query.message.reply_text(stream_info)
        except Exception as e:
            logger.error(f"Channel selection error: {e}")
            await query.message.reply_text("Error retrieving channel details.")

    def run(self):
        """Initialize and run the bot"""
        try:
            application = Application.builder().token(self.token).build()

            # Register handlers
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("search", self.search_command))
            application.add_handler(CallbackQueryHandler(self.channel_selection))

            # Start the bot
            logger.info("Starting bot...")
            application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")

def main():
    bot = ChannelStreamBot(BOT_TOKEN)
    bot.run()

if __name__ == '__main__':
    main()
