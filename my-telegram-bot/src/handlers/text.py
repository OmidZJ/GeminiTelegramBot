import logging
from bot import bot
from utils.logging_config import configure_logging

def register_text_handlers(bot):
    @bot.message_handler(func=lambda message: message.content_type == 'text')
    def handle_text(message):
        retries = 3
        for attempt in range(retries):
            try:
                user_input = message.text
                logging.info(f"User {message.from_user.id} sent text: {user_input}")
                response = current_model.generate_content(user_input)
                send_response(message, response.text)
                break
            except Exception as e:
                logging.exception(f"Error in text handling (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    bot.reply_to(message, "An error occurred after multiple retries. Please try again later.")