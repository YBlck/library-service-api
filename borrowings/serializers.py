from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrowing_date",
            "expected_return_date",
            "actual_return_date",
            "book",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Borrowing
        fields = ("book", "expected_return_date")

    def validate_book(self, book):
        if book.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock")
        return book


class BorrowingListSerializer(BorrowingSerializer):
    book = serializers.SlugRelatedField(read_only=True, slug_field="title")


class BorrowingDetailSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
