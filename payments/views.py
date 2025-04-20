import stripe
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentListSerializer,
    PaymentDetailSerializer,
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
        if self.action == "retrieve":
            return PaymentDetailSerializer
        return PaymentSerializer

    @action(detail=False, methods=["GET"], url_path="success")
    def success(self, request):
        """Endpoint for successful payments."""
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response({"error": "Missing session_id"}, status=400)

        session = stripe.checkout.Session.retrieve(session_id)
        transaction_type = session["metadata"]["transaction_type"]

        if session.payment_status == "paid":
            try:
                payment = Payment.objects.get(session_id=session_id)
                payment.status = Payment.PaymentStatus.PAID
                payment.save()
                if transaction_type == Payment.TransactionType.FINE:
                    payment.borrowing.return_borrowing()
                return Response({"message": "Payment successful"})
            except Payment.DoesNotExist:
                return Response({"error": "Payment not found"}, status=404)
        return Response({"error": "Payment not completed"}, status=400)

    @action(detail=False, methods=["GET"], url_path="cancel")
    def cancel(self, request):
        """Endpoint for cancel payment."""
        return Response(
            {"message": "Payment canceled. You can retry within 24h."},
            status=status.HTTP_200_OK,
        )
