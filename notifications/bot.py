import logging
from os import getenv

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
CHAT_ID = getenv("CHAT_ID")

bot = Bot(token=TOKEN)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def send_notification(message: str):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info("Message sent to Telegram")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")
