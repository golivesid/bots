import os
from flask import Flask, request
import telebot
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask Web Server for Webhook
app = Flask(__name__)

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CRICKET_API_KEY = os.getenv('CRICKET_API_KEY')
WEBHOOK_HOST = os.getenv('WEBHOOK_URL', 'https://your-koyeb-app-url.koyeb.app')

# Initialize Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

class IPLScoreBot:
    def __init__(self, bot_token, cricket_api_key):
        self.bot = bot
        self.cricket_api_key = cricket_api_key
        self.register_handlers()

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            welcome_text = """
            🏏 IPL Live Score Bot 🏏
            
            Available Commands:
            /live_matches - Get current live matches
            /score <match_id> - Get live score for a specific match
            /help - Show help menu
            """
            self.bot.reply_to(message, welcome_text)

        @self.bot.message_handler(commands=['live_matches'])
        def list_live_matches(message):
            try:
                # Fetch live matches (similar to previous implementation)
                matches = self.get_live_matches()
                
                if not matches:
                    self.bot.reply_to(message, "No live matches at the moment.")
                    return
                
                response = "🏏 Live Matches:\n\n"
                for match in matches:
                    response += f"Match ID: {match['unique_id']}\n"
                    response += f"{match['team-1']} vs {match['team-2']}\n"
                    response += f"Status: {match.get('matchStarted', 'Not Started')}\n\n"
                
                self.bot.reply_to(message, response)
            
            except Exception as e:
                self.bot.reply_to(message, f"Error fetching matches: {str(e)}")

        @self.bot.message_handler(commands=['score'])
        def get_match_score(message):
            try:
                match_id = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else None
                
                if not match_id:
                    self.bot.reply_to(message, "Please provide a match ID. Use /live_matches to get match IDs.")
                    return
                
                score_details = self.get_live_score(match_id)
                
                if not score_details:
                    self.bot.reply_to(message, "Unable to fetch score. Check the match ID.")
                    return
                
                response = self.format_score_response(score_details)
                self.bot.reply_to(message, response)
            
            except Exception as e:
                self.bot.reply_to(message, f"Error fetching score: {str(e)}")

    def get_live_matches(self):
        try:
            url = "https://cricapi.com/api/matches"
            params = {'apikey': self.cricket_api_key}
            
            response = requests.get(url, params=params)
            data = response.json()
            
            live_matches = [
                match for match in data.get('matches', []) 
                if match.get('matchStarted') and 'IPL' in match.get('type', '')
            ]
            
            return live_matches
        
        except Exception as e:
            print(f"Error fetching live matches: {e}")
            return []

    def get_live_score(self, match_id):
        try:
            url = "https://cricapi.com/api/cricketScore"
            params = {
                'apikey': self.cricket_api_key,
                'unique_id': match_id
            }
            
            response = requests.get(url, params=params)
            return response.json()
        
        except Exception as e:
            print(f"Error fetching live score: {e}")
            return None

    def format_score_response(self, score_details):
        try:
            response = "🏏 Live Score Update 🏏\n\n"
            response += f"Match: {score_details.get('team-1', 'Team 1')} vs {score_details.get('team-2', 'Team 2')}\n"
            response += f"Score: {score_details.get('score', 'N/A')}\n"
            response += f"Status: {score_details.get('matchStarted', 'Not Started')}\n"
            response += f"Innings: {score_details.get('innings-name', 'N/A')}\n"
            
            return response
        
        except Exception as e:
            print(f"Error formatting score: {e}")
            return "Unable to format score details."

# Initialize Bot
ipl_bot = IPLScoreBot(BOT_TOKEN, CRICKET_API_KEY)

# Webhook Route
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    """Process webhook calls"""
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "OK", 200

# Set Webhook
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    """Set webhook for Telegram Bot"""
    webhook_url = f"{WEBHOOK_HOST}/{BOT_TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return "Webhook set successfully!", 200

# Health Check Route
@app.route('/', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return "IPL Score Bot is running!", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
