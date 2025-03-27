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
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import socket

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = '8063753854:AAE4mAxHO1X4xV0X_l334rS_rZJ_NWQz3VU'
MAX_SEARCH_RESULTS = 10
WEB_SERVER_PORT = 8000

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='players', **kwargs)

    def do_GET(self):
        # Allow serving files from the 'players' directory
        super().do_GET()

def find_free_port():
    """Find a free port for the web server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def start_web_server(port):
    """Start a simple HTTP server in a separate thread"""
    try:
        server_address = ('', port)
        httpd = HTTPServer(server_address, CustomHTTPRequestHandler)
        logger.info(f"Serving player files on port {port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"Web server error: {e}")

class ChannelStreamBot:
    def __init__(self, token: str):
        self.token = token
        self.channels = self.load_channels()
        self.web_port = find_free_port()
        self.generate_player_pages()
        
        # Start web server in a separate thread
        web_thread = threading.Thread(target=start_web_server, args=(self.web_port,), daemon=True)
        web_thread.start()

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
            
            # Generate filename based on channel name
            filename = f"players/{channel['name'].lower().replace(' ', '_')}_player.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(player_html)

    async def channel_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel selection callback"""
        query = update.callback_query
        await query.answer()

        try:
            channel_index = int(query.data.split('_')[1])
            selected_channel = self.channels[channel_index]
            
            # Generate a unique player URL
            player_url = f"http://localhost:{self.web_port}/{selected_channel['name'].lower().replace(' ', '_')}_player.html"
            
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

    # ... (rest of the previous implementation remains the same)

def main():
    bot = ChannelStreamBot(BOT_TOKEN)
    bot.run()

if __name__ == '__main__':
    main()
