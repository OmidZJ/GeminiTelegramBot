import io
import os
import time
import base64
import logging
import requests
import tempfile
from PIL import Image
import telebot
import google.generativeai as genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys
TELEGRAM_BOT_TOKEN = "8036164422:AAE_ZK2MlenkUh1_z9CtOXuSPpjX17dm_AU"
GEMINI_API_KEY = "AIzaSyCE_hJGEaGCgQJOYxJE1wwXBIDaXGjPPKQ"

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    print("Error: Set TELEGRAM_BOT_TOKEN and GEMINI_API_KEY as environment variables.")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Define available models
available_models = {
    "gemini-2.0-flash-thinking-exp-01-21": genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21"),
    "gemini-2.0-flash-exp": genai.GenerativeModel("gemini-2.0-flash-exp"),
    "gemini-1.5-flash": genai.GenerativeModel("gemini-1.5-flash"),
    "gemini-1.5-flash-8b": genai.GenerativeModel("gemini-1.5-flash-8b"),
    "gemini-1.5-pro": genai.GenerativeModel("gemini-1.5-pro")
}
current_model = available_models["gemini-1.5-flash"]

# Cache for user files
user_files = {}

# Initialize Telegram Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# --- Helper Functions ---

TELEGRAM_CHAR_LIMIT = 4096

def split_message(text):
    """Splits a message into chunks smaller than the Telegram character limit."""
    if len(text) <= TELEGRAM_CHAR_LIMIT:
        return [text]
    parts = []
    while len(text) > TELEGRAM_CHAR_LIMIT:
        split_idx = text.rfind('.', 0, TELEGRAM_CHAR_LIMIT)
        if split_idx == -1:
            split_idx = TELEGRAM_CHAR_LIMIT
        parts.append(text[:split_idx + 1])
        text = text[split_idx + 1:].lstrip()
    if text:
        parts.append(text)
    return parts

def format_text_as_telegram(text):
    """Formats text for Telegram, handling markdown for bold and italics."""
    text = text.replace("**", "#").replace("*", "_").replace("#", "*")
    return text

def get_file_info(message):
    if message.photo:
        return message.photo[-1].file_id, "image"
    elif message.document:
        return message.document.file_id, message.document.mime_type
    elif message.audio:
        return message.audio.file_id, "audio"
    elif message.video:
        return message.video.file_id, "video"
    return None, None

def download_file(file_id):
    file_info = bot.get_file(file_id)
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_info.file_path}"
    response = requests.get(download_url)
    if response.status_code == 200:
        logging.info("File downloaded successfully!")
        return response.content
    else:
        logging.error(f"Error downloading file. Status code: {response.status_code}")
        return None

def send_response(message, response_text):
    # Prefix the response with the active model name and two newlines.
    model_name = next((name for name, model in available_models.items() if model == current_model), "unknown-model")
    full_text = f"[{model_name}]:\n\n{response_text}"
    formatted_text = format_text_as_telegram(full_text)
    for chunk in split_message(formatted_text):
        bot.reply_to(message, chunk, parse_mode="Markdown")
# --- Command Handlers ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "ارسال پیام، یا رسانه (تصویر، صدا، ویدیو، سند) با توضیحات اختیاری. از هوش مصنوعی استفاده می‌کنم.\n\n"
        "دستورات:\n/models - فهرست مدل‌ها\n/setmodel <نام_مدل> - تنظیم مدل (مثال: /setmodel gemini-1.5-flash)"
        "\n/generate_image <پرامپت> - تولید تصویر با پرامپت (مثال: /generate_image یک گربه در حال بازی با توپ)"
    )
    bot.reply_to(message, help_text)

model_commands = {
    "/model_gemini2_flash_thinking": "gemini-2.0-flash-thinking-exp-01-21",
    "/model_gemini2_flash": "gemini-2.0-flash-exp",
    "/model_gemini1point5_flash": "gemini-1.5-flash",
    "/model_gemini1point5_flash8b": "gemini-1.5-flash-8b",
    "/model_gemini1point5_pro": "gemini-1.5-pro"
}

@bot.message_handler(commands=['models'])
def list_models(message):
    commands_list = "\n".join(model_commands.keys())
    bot.reply_to(message, f"برای تغییر مدل، روی یکی از گزینه‌های زیر کلیک کنید:\n{commands_list}")

@bot.message_handler(func=lambda message: message.text in model_commands)
def handle_model_change(message):
    try:
        new_model_name = model_commands[message.text]
        global current_model
        current_model = available_models[new_model_name]
        bot.reply_to(message, f"مدل با موفقیت به {new_model_name} تغییر یافت.")
    except Exception as e:
        logging.error(f"خطا در تغییر مدل: {e}")
        bot.reply_to(message, "خطا در تغییر مدل. لطفاً دوباره امتحان کنید.")

@bot.message_handler(commands=['image'])
def generate_image(message):
    try:
        prompt = message.text.replace('/image', '').strip()
        if not prompt:
            bot.reply_to(
                message,
                "لطفا متن مورد نظر برای تولید تصویر را وارد کنید. مثال:\n/image a beautiful sunset"
            )
            return

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_image(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImageConfig(
                negative_prompt='people',
                number_of_images=4,
                include_rai_reason=True,
                output_mime_type='image/jpeg'
            )
        )

        # Use the first generated image from the response
        image = response.generated_images[0].image
        image_bytes = io.BytesIO()
        image.save(image_bytes, format='JPEG')
        image_bytes.seek(0)
        bot.send_photo(message.chat.id, image_bytes)

    except Exception as e:
        logging.error(f"Error generating image: {str(e)}")
        bot.reply_to(message, "متاسفانه در تولید تصویر خطایی رخ داد. لطفا دوباره تلاش کنید.")
        
@bot.message_handler(commands=['generate_image'])
def handle_image_generation(message):
    try:
        user_id = message.from_user.id
        prompt = message.text.split('/generate_image ', 1)[1]
        logging.info(f"User {user_id} requested image generation with prompt: '{prompt}'")

        model = genai.GenerativeModel('imagegeneration@001')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                stop_sequences=[],
                max_output_tokens=4096,
                temperature=1,
            ),
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            image_data = io.BytesIO(response.candidates[0].content.parts[0].blob_data)
            bot.send_photo(message.chat.id, photo=image_data, caption="Generated image")
        else:
            logging.error("Invalid response structure or missing image data.")

    except Exception as e:
        logging.exception(f"Error in image generation: {e}")
        bot.reply_to(message, "Error generating image. Please try again.")

# --- Media Handlers ---

@bot.message_handler(content_types=['photo', 'document', 'audio', 'video'])
def handle_media(message):
    try:
        user_id = message.from_user.id
        file_id, file_type = get_file_info(message)
        if file_id:
            file_content = download_file(file_id)
            user_files[user_id] = (file_content, file_type)
            logging.info(f"User {user_id} sent a {file_type} (file_id: {file_id}). Caption: {message.caption}")

        caption = message.caption if message.caption else ""
        if file_type == 'application/pdf':
            process_pdf(message, file_content, caption)
        else:
            process_with_caption(message, file_content, file_type, caption)

    except Exception as e:
        logging.error(f"Error in media management: {e}")
        bot.reply_to(message, "Error managing file. Please try again.")

def process_pdf(message, file_content, caption):
    user_id = message.from_user.id
    logging.info(f"User {user_id} sent a PDF with caption: '{caption}'")
    try:
        encoded_pdf = base64.b64encode(file_content).decode('utf-8')
        response = current_model.generate_content(
            [
                {'mime_type': 'application/pdf', 'data': encoded_pdf},
                caption
            ]
        )
        send_response(message, response.text)
    except Exception as e:
        logging.exception(f"Error processing PDF: {e}")
        bot.reply_to(message, "Error processing. Please try again.")

def process_with_caption(message, file_content, file_type, caption):
    user_id = message.from_user.id
    logging.info(f"User {user_id} sent {file_type} with caption: '{caption}'")
    try:
        if file_type == 'video':
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmpfile:
                tmpfile.write(file_content)
                video_path = tmpfile.name
            response = current_model.generate_content([caption, video_path])
            os.remove(video_path)
        else:
            image = Image.open(io.BytesIO(file_content))
            response = current_model.generate_content([caption, image])
        send_response(message, response.text)
    except Exception as e:
        logging.exception(f"Error processing media with caption: {e}")
        bot.reply_to(message, "Error processing. Please try again.")

# --- Text Message Handler ---

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

# --- Start Bot ---
if __name__ == "__main__":
    print("Bot started...")

    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")