import datetime
from unittest import TestCase
from unittest.mock import patch

from borrowings.models import Borrowing, Book
from users.models import User
from notifications.telegram_bot import send_notification, borrowing_create_notification


class TelegramNotificationTest(TestCase):
    @patch("notifications.telegram_bot.bot.send_message")
    def test_send_notification_success(self, mock_send):
        send_notification("Test message")
        mock_send.assert_called_once()

    @patch("notifications.telegram_bot.bot.send_message", side_effect=Exception("Bot error"))
    def test_send_notification_failure(self, mock_send):
        send_notification("This will fail")
        mock_send.assert_called_once()

    @patch("notifications.telegram_bot.send_notification")
    def test_borrowing_create_notification(self, mock_send_notification):
        user = User(email="test@example.com")
        book = Book(title="Test Book", inventory=3)
        borrowing = Borrowing(
            user=user,
            book=book,
            borrowing_date=datetime.date.today(),
            expected_return_date=datetime.date.today() + datetime.timedelta(days=7),
        )

        borrowing_create_notification(borrowing)
        self.assertTrue(mock_send_notification.called)
        message_arg = mock_send_notification.call_args[0][0]
        self.assertIn("New borrowing created", message_arg)
        self.assertIn("test@example.com", message_arg)
        self.assertIn("Test Book", message_arg)
