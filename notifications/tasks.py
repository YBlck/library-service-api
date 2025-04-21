import datetime
from borrowings.models import Borrowing
from notifications.telegram_bot import send_notification


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
