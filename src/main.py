import os
import json
import telebot
import logging
from flask import Flask, render_template, request, send_file
from werkzeug.serving import run_simple
import requests

# Load configuration
with open('config.json', 'r') as config_file:
    CONFIG = json.load(config_file)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Telegram Bot
BOT_TOKEN = CONFIG.get('telegram_bot_token')
bot = telebot.TeleBot(BOT_TOKEN)

# Load channels from JSON
def load_channels():
    with open('channels.json', 'r') as f:
        return json.load(f)

# Flask Web Server
app = Flask(__name__)

@app.route('/')
def index():
    channels = load_channels()
    return render_template('index.html', channels=channels)

@app.route('/play')
def play_channel():
    channel_url = request.args.get('url')
    return render_template('player.html', channel_url=channel_url)

@app.route('/proxy_stream')
def proxy_stream():
    stream_url = request.args.get('url')
    try:
        # Proxy the stream
        response = requests.get(stream_url, stream=True)
        return response.raw.read(), response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Stream proxy error: {e}")
        return "Stream unavailable", 500

# Telegram Bot Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    channels = load_channels()
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [telebot.types.KeyboardButton(channel['name']) for channel in channels]
    keyboard.add(*buttons)
    
    welcome_message = "Welcome! Choose a channel to stream:"
    bot.send_message(message.chat.id, welcome_message, reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle_channel_selection(message):
    channels = load_channels()
    selected_channel = next((ch for ch in channels if ch['name'] == message.text), None)
    
    if selected_channel:
        # Create inline keyboard for streaming methods
        markup = telebot.types.InlineKeyboardMarkup()
        
        # Direct stream buttons
        jwplayer_button = telebot.types.InlineKeyboardButton(
            "JW Player Stream", 
            callback_data=f"stream_jwplayer:{selected_channel['jwplayer_url']}"
        )
        m3u8_button = telebot.types.InlineKeyboardButton(
            "M3U8 Stream", 
            callback_data=f"stream_m3u8:{selected_channel['m3u8_url']}"
        )
        markup.row(jwplayer_button, m3u8_button)
        
        # Send message with streaming options
        bot.send_message(
            message.chat.id, 
            f"Select streaming method for {selected_channel['name']}:", 
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "Channel not found. Please choose from the list.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('stream_'))
def handle_stream_callback(call):
    try:
        # Parse the callback data
        stream_type, stream_url = call.data.split(':')
        
        # Create an inline keyboard for the stream
        markup = telebot.types.InlineKeyboardMarkup()
        web_player_button = telebot.types.InlineKeyboardButton(
            "Open Web Player", 
            url=f"https://your-domain.com/play?url={stream_url}"
        )
        markup.add(web_player_button)
        
        # Send a message with the stream details
        bot.answer_callback_query(call.id, "Preparing stream...")
        bot.send_message(
            call.message.chat.id, 
            f"Stream URL: {stream_url}\n\n"
            "Click 'Open Web Player' to watch:",
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Stream callback error: {e}")
        bot.answer_callback_query(call.id, "Error processing stream")

def start_bot_and_server():
    # Start Flask server in a separate thread
    from threading import Thread
    flask_thread = Thread(target=lambda: run_simple('0.0.0.0', 5000, app))
    flask_thread.start()
    
    # Start Telegram Bot
    bot.polling(none_stop=True)

if __name__ == '__main__':
    start_bot_and_server()
