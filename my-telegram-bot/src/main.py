import os
import telebot
from bot import bot
from handlers.commands import register_command_handlers
from handlers.media import register_media_handlers
from handlers.text import register_text_handlers

def main():
    register_command_handlers(bot)
    register_media_handlers(bot)
    register_text_handlers(bot)

    print("Bot started...")
    bot.infinity_polling()

if __name__ == "__main__":
    main()