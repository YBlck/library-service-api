from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
)


class PaymentsViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if self.action in ["retrieve", "list"]:
            if user.is_staff:
                return queryset
            return queryset.filter(borrowing__user__id=user.id)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentSerializer
