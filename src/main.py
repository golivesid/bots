import os
import json
import requests
import telebot
from flask import Flask, render_template, request
from flask_cors import CORS

# Telegram Bot Token - Replace with your actual bot token
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# GitHub JSON file URL with channel information
CHANNELS_JSON_URL = 'https://raw.githubusercontent.com/seeubot/bots/refs/heads/main/channels.json'

# Initialize Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Function to fetch channels from GitHub
def fetch_channels():
    try:
        response = requests.get(CHANNELS_JSON_URL)
        return response.json()
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return {}

# Telegram Bot Commands (same as previous version)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
Welcome to Live TV Channels Bot! 🌐📺
Available commands:
/channels - List all available channels
/play [channel_name] - Play a specific channel
/categories - Show channel categories
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['channels'])
def list_channels(message):
    channels = fetch_channels().get('channels', [])
    channel_list = "\n".join([f"{channel['name']} - {channel.get('category', 'Uncategorized')}" for channel in channels])
    bot.reply_to(message, f"Available Channels:\n{channel_list}")

@bot.message_handler(commands=['categories'])
def list_categories(message):
    channels = fetch_channels().get('channels', [])
    categories = set(channel.get('category', 'Uncategorized') for channel in channels)
    category_list = "\n".join(sorted(categories))
    bot.reply_to(message, f"Channel Categories:\n{category_list}")

@bot.message_handler(commands=['play'])
def play_channel(message):
    try:
        channel_name = message.text.split(' ', 1)[1].strip()
        channels = fetch_channels().get('channels', [])
        
        matching_channels = [channel for channel in channels if channel['name'].lower() == channel_name.lower()]
        
        if matching_channels:
            channel = matching_channels[0]
            # Support multiple player types
            player_url = f"/player?url={channel['url']}&drm_key_id={channel.get('drm_key_id', '')}&drm_key={channel.get('drm_key', '')}"
            response = f"Playing {channel['name']}\nClick the link to watch: {player_url}"
            bot.reply_to(message, response)
        else:
            bot.reply_to(message, f"Channel '{channel_name}' not found.")
    except IndexError:
        bot.reply_to(message, "Please specify a channel name. Usage: /play CNN")

# Web Player Route
@app.route('/player')
def video_player():
    stream_url = request.args.get('url', '')
    drm_key_id = request.args.get('drm_key_id', '')
    drm_key = request.args.get('drm_key', '')
    return render_template('player.html', 
                           stream_url=stream_url, 
                           drm_key_id=drm_key_id, 
                           drm_key=drm_key)

# HTML5 Video Player Template with JW Player and HLS Support
def create_player_template():
    player_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Live TV Player</title>
    <style>
        body { 
            margin: 0; 
            background-color: black; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh;
            font-family: Arial, sans-serif;
        }
        #playerContainer {
            width: 100%;
            max-width: 1280px;
            max-height: 720px;
        }
        #playerTabs {
            display: flex;
            justify-content: center;
            margin-bottom: 10px;
        }
        .playerTab {
            padding: 10px 20px;
            margin: 0 5px;
            background-color: #333;
            color: white;
            cursor: pointer;
            border-radius: 5px;
        }
        .playerTab.active {
            background-color: #555;
        }
        .playerContent {
            display: none;
        }
        .playerContent.active {
            display: block;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script src="https://content.jwplatform.com/libraries/SAHhwvZq.js"></script>
</head>
<body>
    <div id="playerContainer">
        <div id="playerTabs">
            <div class="playerTab active" data-player="hls">HLS Player</div>
            <div class="playerTab" data-player="jwplayer">JW Player</div>
        </div>
        
        <div id="hlsPlayerContent" class="playerContent active">
            <video id="hlsVideoPlayer" controls autoplay style="width:100%;">
                <source src="{{ stream_url }}" type="application/x-mpegURL">
                Your browser does not support the video tag.
            </video>
        </div>
        
        <div id="jwPlayerContent" class="playerContent">
            <div id="jwplayerDiv"></div>
        </div>
    </div>

    <script>
        // HLS Player Logic
        var hlsVideo = document.getElementById('hlsVideoPlayer');
        var streamUrl = '{{ stream_url }}';
        
        if (Hls.isSupported()) {
            var hls = new Hls();
            hls.loadSource(streamUrl);
            hls.attachMedia(hlsVideo);
            hls.on(Hls.Events.MANIFEST_PARSED, function() {
                hlsVideo.play();
            });
        } else if (hlsVideo.canPlayType('application/vnd.apple.mpegurl')) {
            hlsVideo.src = streamUrl;
            hlsVideo.addEventListener('loadedmetadata', function() {
                hlsVideo.play();
            });
        }

        // JW Player Logic
        var jwPlayerConfig = {
            file: '{{ stream_url }}',
            type: '{% if drm_key_id and drm_key %}dash{% else %}hls{% endif %}',
            {% if drm_key_id and drm_key %}
            drm: {
                "clearkey": {
                    "keyId": "{{ drm_key_id }}",
                    "key": "{{ drm_key }}"
                }
            },
            {% endif %}
        };
        
        jwplayer("jwplayerDiv").setup(jwPlayerConfig);

        // Player Tab Switching Logic
        document.querySelectorAll('.playerTab').forEach(tab => {
            tab.addEventListener('click', function() {
                // Remove active class from all tabs and contents
                document.querySelectorAll('.playerTab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.playerContent').forEach(c => c.classList.remove('active'));
                
                // Add active class to clicked tab and corresponding content
                this.classList.add('active');
                document.getElementById(this.dataset.player + 'PlayerContent').classList.add('active');
            });
        });
    </script>
</body>
</html>
    """
    
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    # Write player template
    with open('templates/player.html', 'w') as f:
        f.write(player_html)

# Rest of the code remains the same as in the previous version
# (Bot commands, main execution, etc.)

# Main execution
if __name__ == '__main__':
    create_player_template()
    
    # Start bot in a separate thread
    import threading
    bot_thread = threading.Thread(target=bot.polling)
    bot_thread.start()
    
    # Run Flask web server
    app.run(port=5000)
