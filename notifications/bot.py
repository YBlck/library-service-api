from os import getenv

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
CHAT_ID = getenv("CHAT_ID")

bot = Bot(token=TOKEN)


def send_notification(message: str):
    bot.send_message(chat_id=CHAT_ID, text=message)
