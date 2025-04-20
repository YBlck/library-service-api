import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q, F

from books.models import Book


class Borrowing(models.Model):
    borrowing_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowings"
    )

    def __str__(self):
        return (
            f"{self.borrowing_date}-{self.book}-"
            f"{self.user}-{self.expected_return_date}"
        )

    class Meta:
        ordering = ["expected_return_date"]
        constraints = [
            models.CheckConstraint(
                check=Q(expected_return_date__gte=F("borrowing_date")),
                name="expected_return_date_gte_borrowing_date",
            ),
            models.CheckConstraint(
                check=Q(actual_return_date__gte=F("borrowing_date")),
                name="actual_return_date_gte_borrowing_date",
            ),
        ]

    def get_duration_days(self):
        return (self.expected_return_date - self.borrowing_date).days

    def get_overdue_days(self):
        return (self.actual_return_date - self.expected_return_date).days

    def return_borrowing(self):
        self.actual_return_date = datetime.date.today()
        self.book.increase_inventory()
        self.book.save()
        self.save()
