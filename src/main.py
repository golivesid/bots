import os
import json
import telebot
from telebot import types
import requests

# Replace with your actual Telegram Bot Token
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

# Load channels from JSON
def load_channels():
    try:
        with open('channels.json', 'r') as file:
            return json.load(file)['channels']
    except Exception as e:
        print(f"Error loading channels: {e}")
        return []

# Search function for channels
def search_channels(query):
    channels = load_channels()
    query = query.lower()
    return [
        channel for channel in channels 
        if query in channel['name'].lower()
    ]

# Create inline keyboard for channel results
def create_channel_keyboard(channels):
    keyboard = types.InlineKeyboardMarkup()
    for channel in channels:
        button = types.InlineKeyboardButton(
            text=channel['name'], 
            callback_data=f"channel_{channels.index(channel)}"
        )
        keyboard.add(button)
    return keyboard

# Handler for search command
@bot.message_handler(commands=['search'])
def search_command(message):
    try:
        # Extract search query
        query = message.text.split(' ', 1)[1]
        
        # Find matching channels
        results = search_channels(query)
        
        if not results:
            bot.reply_to(message, "No channels found matching your search.")
            return
        
        # Create and send inline keyboard with results
        keyboard = create_channel_keyboard(results)
        bot.reply_to(
            message, 
            f"Found {len(results)} channels matching '{query}':", 
            reply_markup=keyboard
        )
    except IndexError:
        bot.reply_to(message, "Please provide a search term. Usage: /search keyword")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

# Handler for channel selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('channel_'))
def channel_selection(call):
    try:
        # Get channels and selected channel index
        channels = load_channels()
        channel_index = int(call.data.split('_')[1])
        selected_channel = channels[channel_index]
        
        # Prepare stream information
        stream_info = f"""
📺 Channel: {selected_channel['name']}
🔗 HLS Stream: {selected_channel['url']}
🔗 DASH Stream: {selected_channel['dash_url']}
        """
        
        # Send stream information
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id, 
            stream_info, 
            parse_mode='HTML'
        )
    except Exception as e:
        bot.answer_callback_query(call.id, text=f"Error: {str(e)}")

# Handler for start command
@bot.message_handler(commands=['start'])
def start_command(message):
    welcome_message = """
Welcome to the Channel Stream Bot! 🎥

Available commands:
• /search [keyword] - Search for channels
• /start - Show this welcome message
• /help - Get help information
    """
    bot.reply_to(message, welcome_message)

# Handler for help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_message = """
🤖 Channel Stream Bot Help

How to use:
1. Use /search to find channels
2. Click on a channel to get stream links
3. Use the stream links in your preferred media player

Example:
/search sports - Finds channels with 'sports' in the name
    """
    bot.reply_to(message, help_message)

# Main bot polling
def run_bot():
    print("Bot is running...")
    bot.polling(none_stop=True)

if __name__ == '__main__':
    run_bot()
