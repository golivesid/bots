import os
import telebot
import requests
from flask import Flask, render_template, jsonify, send_from_directory
import threading

# Telegram Bot Configuration
class TelegramConfig:
    BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'  # Replace with your actual bot token
    STREAM_DETAILS_URL = 'https://raw.githubusercontent.com/your-username/your-repo/main/stream_details.json'
    CACHE_FILE = 'stream_details.json'

# Flask Web Server Configuration
class FlaskConfig:
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True

# Telegram Bot Setup
bot = telebot.TeleBot(TelegramConfig.BOT_TOKEN)

# Flask App Setup
app = Flask(__name__)

def fetch_stream_details():
    """
    Fetch stream details from GitHub or local cache
    """
    try:
        # Attempt to fetch from GitHub
        response = requests.get(TelegramConfig.STREAM_DETAILS_URL)
        response.raise_for_status()
        stream_details = response.json()
        
        # Cache the details locally
        with open(TelegramConfig.CACHE_FILE, 'w') as f:
            import json
            json.dump(stream_details, f)
        
        return stream_details
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        
        # Fallback to local cache if available
        try:
            with open(TelegramConfig.CACHE_FILE, 'r') as f:
                import json
                return json.load(f)
        except FileNotFoundError:
            # If no local cache, return default/empty details
            return {
                "file": "",
                "keyId": "",
                "key": ""
            }

# Flask Routes
@app.route('/')
def index():
    """
    Main route to serve the video player page
    """
    return render_template('index.html')

@app.route('/stream-details')
def get_stream_details():
    """
    API endpoint to retrieve stream details
    """
    stream_details = fetch_stream_details()
    return jsonify(stream_details)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    Serve static files (if needed)
    """
    return send_from_directory('static', filename)

# Telegram Bot Handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Welcome message handler
    """
    welcome_text = """
    Welcome to the Live TV Streaming Bot! 
    Available commands:
    /stream - Get stream details
    /player - Receive HTML player
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['stream'])
def send_stream_link(message):
    """
    Send stream details to user
    """
    stream_details = fetch_stream_details()
    
    if stream_details and stream_details.get('file'):
        stream_info = f"""
🎥 Live TV Stream Details:
File URL: {stream_details['file']}
Key ID: {stream_details.get('keyId', 'N/A')}
        """
        bot.reply_to(message, stream_info)
    else:
        bot.reply_to(message, "Sorry, unable to fetch stream details at the moment.")

@bot.message_handler(commands=['player'])
def send_player_html(message):
    """
    Send HTML player file to user
    """
    stream_details = fetch_stream_details()
    
    if stream_details and stream_details.get('file'):
        # HTML player template
        player_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Live TV Stream</title>
    <script src="https://content.jwplatform.com/libraries/SAHhwvZq.js"></script>
</head>
<body>
    <div id="jwplayerDiv"></div>
    <script>  
    jwplayer("jwplayerDiv").setup({{
        file: "{stream_details['file']}",
        type: "dash",
        drm: {{ 
            "clearkey": {{
                "keyId": "{stream_details.get('keyId', '')}",
                "key": "{stream_details.get('key', '')}"
            }}
        }}
    }});
    </script>
</body>
</html>
        """
        
        # Save HTML to a file
        with open('stream_player.html', 'w') as f:
            f.write(player_html)
        
        # Send the HTML file
        with open('stream_player.html', 'rb') as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.reply_to(message, "Sorry, unable to generate player at the moment.")

# Function to run Telegram Bot
def run_telegram_bot():
    print("Telegram Bot is running...")
    bot.polling(none_stop=True)

# Function to run Flask Web Server
def run_flask_server():
    print("Flask Web Server is running...")
    app.run(
        host=FlaskConfig.HOST,
        port=FlaskConfig.PORT,
        debug=FlaskConfig.DEBUG
    )

# Main Execution
def main():
    # Create threads for bot and web server
    telegram_thread = threading.Thread(target=run_telegram_bot)
    flask_thread = threading.Thread(target=run_flask_server)
    
    # Start both threads
    telegram_thread.start()
    flask_thread.start()
    
    # Wait for both threads to complete
    telegram_thread.join()
    flask_thread.join()

if __name__ == '__main__':
    main()
