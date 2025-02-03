import requests
import logging
from bot import bot

def download_file(file_id):
    file_info = bot.get_file(file_id)
    download_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
    response = requests.get(download_url)
    if response.status_code == 200:
        logging.info("File downloaded successfully!")
        return response.content
    else:
        logging.error(f"Error downloading file. Status code: {response.status_code}")
        return None

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