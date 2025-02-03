import logging
from bot import bot
from utils.file_utils import download_file, get_file_info

def register_media_handlers(bot):
    @bot.message_handler(content_types=['photo', 'document', 'audio', 'video'])
    def handle_media(message):
        try:
            file_id, file_type = get_file_info(message)
            if file_id:
                file_content = download_file(file_id)
                # Process the media file based on its type
                # Additional processing logic goes here
        except Exception as e:
            logging.error(f"Error in media management: {e}")
            bot.reply_to(message, "Error managing file. Please try again.")