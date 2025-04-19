from django.db import transaction
from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from notifications.bot import borrowing_create_notification
from payments.models import Payment
from payments.services import create_checkout_session


class BorrowingPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ("id", "status", "type", "money_to_pay")


class BorrowingSerializer(serializers.ModelSerializer):
    payment = BorrowingPaymentSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrowing_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "payment",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = ("id", "book", "borrowing_date", "expected_return_date")

    def validate_book(self, book):
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock")
        return book

    # thinking about moving creation to ViewSet...
    def create(self, validated_data):
        book = validated_data["book"]

        with transaction.atomic():
            book_for_update = Book.objects.select_for_update().get(pk=book.pk)
            if book_for_update.inventory > 0:
                book_for_update.reduce_inventory()
                borrowing = Borrowing.objects.create(**validated_data)
                create_checkout_session(
                    borrowing, Payment.TransactionType.PAYMENT
                ),
                transaction.on_commit(
                    lambda: borrowing_create_notification(borrowing)
                )
                return borrowing
            else:
                raise serializers.ValidationError("This book is out of stock")


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
            "payment",
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
            "payment",
        )


class BorrowingReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id",)
