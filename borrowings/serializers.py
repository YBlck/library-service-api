from django.db import transaction
from rest_framework import serializers

from books.models import Book
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

    def create(self, validated_data):
        book = validated_data["book"]
        with transaction.atomic():
            book_for_update = Book.objects.select_for_update().get(pk=book.pk)
            if book_for_update.inventory > 0:
                book_for_update.reduce_inventory()
                borrowing = Borrowing.objects.create(**validated_data)
                return borrowing
            else:
                raise serializers.ValidationError("This book is out of stock")


class BorrowingListSerializer(BorrowingSerializer):
    book = serializers.SlugRelatedField(read_only=True, slug_field="title")


class BorrowingDetailSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
