from bot import bot

def register_command_handlers(bot):
    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        help_text = (
            "ارسال پیام، یا رسانه (تصویر، صدا، ویدیو، سند) با توضیحات اختیاری. از هوش مصنوعی استفاده می‌کنم.\n\n"
            "دستورات:\n/models - فهرست مدل‌ها\n/setmodel <نام_مدل> - تنظیم مدل\n/generate_image <پرامپت> - تولید تصویر"
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