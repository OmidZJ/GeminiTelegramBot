import os
import logging
import google.generativeai as genai
import telebot

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("Error: Set TELEGRAM_BOT_TOKEN and GEMINI_API_KEY as environment variables.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)