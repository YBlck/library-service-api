import datetime
import logging
from os import getenv

from dotenv import load_dotenv
from telegram import Bot

from borrowings.models import Borrowing

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
CHAT_ID = getenv("CHAT_ID")

bot = Bot(token=TOKEN)

# logging.basicConfig(
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     level=logging.INFO,
# )


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


def check_overdue_borrowings():
    today = datetime.date.today()
    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lt=today, actual_return_date__isnull=True
    )

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"<b>Overdue borrowing alert!</b>\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}\n"
                f"Expected return: {borrowing.expected_return_date}"
            )
            send_notification(message)
    else:
        send_notification("📢 No borrowings overdue today!")
