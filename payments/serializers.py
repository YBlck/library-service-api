from rest_framework import serializers

from borrowings.serializers import BorrowingListSerializer
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        )


class PaymentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "borrowing",
            "type",
            "status",
            "money_to_pay",
        )


class PaymentDetailSerializer(PaymentSerializer):
    borrowing = BorrowingListSerializer(read_only=True)
