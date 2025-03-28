import os
import logging
import urllib.request
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def download_file(url, save_path=None):
    """
    Download a file using urllib.
    
    Args:
        url (str): URL of the file to download
        save_path (str, optional): Path to save the file. If None, uses the original filename.
    
    Returns:
        str: Path where the file was saved
    """
    try:
        # Create downloads directory if it doesn't exist
        downloads_dir = 'downloads'
        os.makedirs(downloads_dir, exist_ok=True)
        
        # If save_path is not provided, extract filename from URL
        if save_path is None:
            filename = os.path.basename(urlparse(url).path) or 'downloaded_file'
            save_path = os.path.join(downloads_dir, filename)
        
        # Download the file
        print(f"Downloading from: {url}")
        print(f"Saving to: {save_path}")
        
        urllib.request.urlretrieve(url, save_path)
        
        print(f"File successfully downloaded to: {save_path}")
        return save_path
    
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    welcome_message = (
        "Welcome! I can help you download files from URLs and upload them to Telegram. \n\n"
        "Usage:\n"
        "1. Send me a URL to download a file\n"
        "2. I'll download the file and then upload it back to you"
    )
    await update.message.reply_text(welcome_message)

async def download_and_upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Download a file from the given URL and upload it to Telegram.
    """
    # Check if a URL is provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("Please provide a URL to download. Usage: /download <url>")
        return
    
    # Get the URL from the command arguments
    url = context.args[0]
    
    try:
        # Send a waiting message
        waiting_message = await update.message.reply_text("Downloading file... Please wait.")
        
        # Download the file
        downloaded_file_path = download_file(url)
        
        if downloaded_file_path is None:
            await update.message.reply_text("Failed to download the file. Please check the URL and try again.")
            return
        
        # Upload the file to Telegram
        try:
            await update.message.reply_document(
                document=downloaded_file_path,
                caption=f"Here's the file downloaded from: {url}"
            )
        except Exception as upload_error:
            await update.message.reply_text(f"Failed to upload the file: {upload_error}")
        
        # Delete the waiting message
        await waiting_message.delete()
        
        # Optional: Remove the downloaded file after upload
        os.remove(downloaded_file_path)
    
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

async def handle_url_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle direct URL messages.
    """
    # Get the URL from the message
    url = update.message.text.strip()
    
    try:
        # Send a waiting message
        waiting_message = await update.message.reply_text("Downloading file... Please wait.")
        
        # Download the file
        downloaded_file_path = download_file(url)
        
        if downloaded_file_path is None:
            await update.message.reply_text("Failed to download the file. Please check the URL and try again.")
            return
        
        # Upload the file to Telegram
        try:
            await update.message.reply_document(
                document=downloaded_file_path,
                caption=f"Here's the file downloaded from: {url}"
            )
        except Exception as upload_error:
            await update.message.reply_text(f"Failed to upload the file: {upload_error}")
        
        # Delete the waiting message
        await waiting_message.delete()
        
        # Optional: Remove the downloaded file after upload
        os.remove(downloaded_file_path)
    
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")

def main():
    """
    Main function to start the Telegram bot.
    
    IMPORTANT: Replace 'YOUR_BOT_TOKEN' with your actual Telegram Bot Token
    """
    # Create the Application and pass it your bot's token
    application = Application.builder().token('YOUR_BOT_TOKEN').build()
    
    # Register handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('download', download_and_upload_file))
    
    # Add a message handler to capture direct URL messages
    application.add_handler(MessageHandler(
        filters.TEXT & 
        ~filters.COMMAND & 
        filters.Regex(r'^(https?://\S+)$'), 
        handle_url_message
    ))
    
    # Start the Bot
    print("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Create downloads directory
    os.makedirs('downloads', exist_ok=True)
    
    # Run the bot
    main()

# SETUP INSTRUCTIONS:
# 1. Install required libraries:
#    pip install python-telegram-bot
#
# 2. Create a Telegram Bot:
#    - Talk to BotFather on Telegram
#    - Create a new bot and get the token
#    - Replace 'YOUR_BOT_TOKEN' with the token you received
#
# 3. Run the script

# USAGE:
# - Send /start to get instructions
# - Send /download <url> to download a file
# - Or simply send a direct URL
