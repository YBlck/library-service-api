import logging
from os import getenv

from dotenv import load_dotenv
from telegram import Bot

from borrowings.models import Borrowing

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
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
        logging.info("Message sent to Telegram")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")


def borrowing_create_notification(borrowing: Borrowing):
    user = borrowing.user
    book = borrowing.book
    message = (
        f"<b>New borrowing created!</b>\n"
        f"User: {user.email}\n"
        f"Book: {book.title} ({book.inventory - 1} left)\n"
        f"Exp. return date: {borrowing.expected_return_date}\n"
    )
    send_notification(message)
