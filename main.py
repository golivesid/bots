```python
import os
import telebot
import requests
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
from datetime import datetime, timedelta

# Logging Configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
CRICAPI_API_KEY = '7c96d07c-0e63-4d5d-a2b4-dc9520ba9492'  # Get from cricapi.com
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

class IPLLiveScoreBot:
    def __init__(self, bot_token, api_key):
        self.bot = TeleBot(bot_token)
        self.api_key = api_key
        self._register_handlers()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            welcome_text = """
🏏 IPL Live Score Bot 🏆

Available Commands:
/matches - Current Live Matches
/upcoming - Upcoming Matches
/help - Bot Instructions
            """
            self.bot.reply_to(message, welcome_text)

        @self.bot.message_handler(commands=['matches'])
        def live_matches(message):
            matches = self.get_live_matches()
            if matches:
                response = "🔴 Live Matches:\n\n"
                for match in matches:
                    response += self.format_match_details(match)
                self.bot.send_message(message.chat.id, response, parse_mode='HTML')
            else:
                self.bot.reply_to(message, "No live matches at the moment.")

        @self.bot.message_handler(commands=['upcoming'])
        def upcoming_matches(message):
            matches = self.get_upcoming_matches()
            if matches:
                response = "🗓️ Upcoming Matches:\n\n"
                for match in matches:
                    response += self.format_upcoming_match(match)
                self.bot.send_message(message.chat.id, response, parse_mode='HTML')
            else:
                self.bot.reply_to(message, "No upcoming matches found.")

    def get_live_matches(self):
        """
        Fetch live cricket matches using CricAPI
        """
        try:
            url = f"https://cricapi.com/api/matches?apikey={self.api_key}"
            response = requests.get(url)
            data = response.json()
            
            # Filter for live IPL matches
            live_matches = [
                match for match in data.get('matches', []) 
                if match.get('matchStarted') and not match.get('matchEnded') 
                and 'IPL' in match.get('type', '')
            ]
            
            return live_matches
        except Exception as e:
            logger.error(f"Error fetching live matches: {e}")
            return []

    def get_match_score(self, match_id):
        """
        Get detailed score for a specific match
        """
        try:
            url = f"https://cricapi.com/api/cricketScore?apikey={self.api_key}&unique_id={match_id}"
            response = requests.get(url)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching match score: {e}")
            return {}

    def get_upcoming_matches(self):
        """
        Fetch upcoming cricket matches
        """
        try:
            url = f"https://cricapi.com/api/matches?apikey={self.api_key}"
            response = requests.get(url)
            data = response.json()
            
            # Filter for upcoming IPL matches
            upcoming_matches = [
                match for match in data.get('matches', []) 
                if not match.get('matchStarted') 
                and 'IPL' in match.get('type', '')
            ]
            
            return upcoming_matches
        except Exception as e:
            logger.error(f"Error fetching upcoming matches: {e}")
            return []

    def format_match_details(self, match):
        """
        Format live match details
        """
        try:
            # Fetch detailed score
            score_details = self.get_match_score(match.get('unique_id'))
            
            match_info = (
                f"🏏 <b>{match.get('team-1', 'Team 1')} vs {match.get('team-2', 'Team 2')}</b>\n"
                f"📅 {match.get('date', 'Date Not Available')}\n"
            )
            
            # Add score if available
            if score_details and 'score' in score_details:
                match_info += f"📊 Score: {score_details.get('score', 'Score Not Available')}\n"
            
            match_info += f"🏆 Type: {match.get('type', 'Unknown')}\n\n"
            
            return match_info
        except Exception as e:
            logger.error(f"Error formatting match details: {e}")
            return ""

    def format_upcoming_match(self, match):
        """
        Format upcoming match details
        """
        return (
            f"🏏 <b>{match.get('team-1', 'Team 1')} vs {match.get('team-2', 'Team 2')}</b>\n"
            f"📅 {match.get('date', 'Date Not Available')}\n"
            f"🏆 Type: {match.get('type', 'Unknown')}\n\n"
        )

    def start_bot(self):
        """
        Start the Telegram bot
        """
        logger.info("IPL Live Score Bot Started!")
        self.bot.polling(none_stop=True)

def main():
    try:
        # Initialize and start the bot
        bot = IPLLiveScoreBot(
            bot_token=BOT_TOKEN, 
            api_key=CRICAPI_API_KEY
        )
        bot.start_bot()
    except Exception as e:
        logger.critical(f"Bot initialization failed: {e}")

if __name__ == '__main__':
    main()
```
