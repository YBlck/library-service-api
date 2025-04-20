import datetime

from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing
from payments.models import Payment


class BorrowingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "status", "type", "money_to_pay", "session_url")


class BorrowingSerializer(serializers.ModelSerializer):
    payments = BorrowingPaymentSerializer(read_only=True, many=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrowing_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "payments",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = ("id", "book", "borrowing_date", "expected_return_date")

    def validate_book(self, book):
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock")
        return book

    def validate_expected_return_date(self, expected_return_date):
        if expected_return_date < datetime.date.today():
            raise serializers.ValidationError(
                "The expected return date cannot precede the borrowing date."
            )
        return expected_return_date

    def validate_actual_return_date(self, actual_return_date):
        if actual_return_date < datetime.date.today():
            raise serializers.ValidationError(
                "The actual return date cannot precede the borrowing date."
            )
        return actual_return_date


class BorrowingListSerializer(BorrowingSerializer):
    book = serializers.SlugRelatedField(read_only=True, slug_field="title")


class BorrowingListAdminSerializer(BorrowingListSerializer):

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrowing_date",
            "expected_return_date",
            "actual_return_date",
            "user",
            "book",
            "payments",
        )


class BorrowingDetailSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)


class BorrowingDetailAdminSerializer(BorrowingDetailSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrowing_date",
            "expected_return_date",
            "actual_return_date",
            "user",
            "book",
            "payments",
        )


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id",)
