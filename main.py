import logging
from bot_instance import bot

# ✅ Configure logging to display in PowerShell AND optionally save to file
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Import handlers to register them
import handlers.start
import handlers.faqs
import handlers.support
import handlers.tracking
import handlers.uploads
import handlers.payment
import handlers.media
import handlers.broadcast

if __name__ == '__main__':
    logging.info("🚀 Bot starting up...")  # ✅ THIS WILL PRINT AND SAVE
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logging.error(f"❌ Telegram polling error: {e}\nPlease ensure no other bot instance is running.")
