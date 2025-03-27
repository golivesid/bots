import os
from flask import Flask, request
import telebot
import requests
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CRICKET_API_KEY = os.getenv('CRICKET_API_KEY')
WEBHOOK_HOST = os.getenv('WEBHOOK_URL', 'https://your-koyeb-app-url.koyeb.app')

# Create Flask application
app = Flask(__name__)

class IPLScoreBot:
    def __init__(self, bot_token, cricket_api_key):
        self.bot = telebot.TeleBot(bot_token)
        self.cricket_api_key = cricket_api_key
        self.register_handlers()

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            welcome_text = """
            🏏 IPL Live Score Bot 🏏
            
            To get live ball-by-ball updates, join our channel: @terao2
            
            Available Commands:
            /live_matches - Get current live matches
            /score <match_id> - Get live score for a specific match
            /help - Show help menu
            """
            # Create inline keyboard
            markup = InlineKeyboardMarkup()
            watch_button = InlineKeyboardButton("🏏 Watch IPL Live", url="https://t.me/terao2")
            markup.add(watch_button)
            
            self.bot.reply_to(message, welcome_text, reply_markup=markup)

        # Other handler methods remain the same as in previous implementations

    # Other class methods remain the same

# Initialize Bot
ipl_bot = IPLScoreBot(BOT_TOKEN, CRICKET_API_KEY)

# Webhook Route
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Process webhook calls"""
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    ipl_bot.bot.process_new_updates([update])
    return "OK", 200

# Set Webhook
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    """Set webhook for Telegram Bot"""
    webhook_url = f"{WEBHOOK_HOST}/{BOT_TOKEN}"
    ipl_bot.bot.remove_webhook()
    ipl_bot.bot.set_webhook(url=webhook_url)
    return "Webhook set successfully!", 200

# Health Check Route
@app.route('/', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return "IPL Score Bot is running!", 200

# Main entry point
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='https://hushed-nance-seeutech-79662458.koyeb.app', port=port)
