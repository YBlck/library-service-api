import datetime

from django.db import transaction
from django.http import HttpRequest
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingListAdminSerializer,
    BorrowingDetailAdminSerializer,
    BorrowingReturnSerializer,
)
from notifications.telegram import borrowing_create_notification
from payments.models import Payment
from payments.services import create_checkout_session


class BorrowingViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if not user.is_staff:
            queryset = self.queryset.filter(user=user)

        status = self.request.query_params.get("is_active")
        user_id = self.request.query_params.get("user_id")

        if status:
            queryset = queryset.filter(actual_return_date__isnull=True)

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            if self.request.user.is_staff:
                return BorrowingListAdminSerializer
            return BorrowingListSerializer

        if self.action == "retrieve":
            if self.request.user.is_staff:
                return BorrowingDetailAdminSerializer
            return BorrowingDetailSerializer

        if self.action == "create":
            return BorrowingCreateSerializer

        if self.action == "return_book":
            return BorrowingReturnSerializer

        return BorrowingSerializer

    def create(self, request: HttpRequest, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.validated_data["book"]

        with transaction.atomic():
            book_for_update = Book.objects.select_for_update().get(pk=book.pk)
            if book_for_update.inventory > 0:
                book_for_update.reduce_inventory()
                borrowing = Borrowing.objects.create(
                    book=book,
                    borrowing_date=serializer.validated_data.get(
                        "borrowing_date"
                    ),
                    expected_return_date=serializer.validated_data.get(
                        "expected_return_date"
                    ),
                    user=request.user,
                )
                payment_url = create_checkout_session(
                    borrowing, Payment.TransactionType.PAYMENT, request
                )
                transaction.on_commit(
                    lambda: borrowing_create_notification(borrowing)
                )
                return Response(
                    {
                        "borrowing": self.get_serializer(borrowing).data,
                        "payment_url": payment_url,
                    },
                    status=201,
                )
            else:
                return Response(
                    {"error": "This book is out of stock"}, status=400
                )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_active",
                description="Filter borrowings by status",
                type=OpenApiTypes.BOOL,
                required=False,
            ),
            OpenApiParameter(
                name="user_id",
                description="Filter borrowings by user_id",
                type=OpenApiTypes.INT,
                required=False,
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get list of borrowings"""
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["POST"], url_path="return")
    def return_book(self, request, pk=None):
        """Endpoint for borrowing return functionality"""
        borrowing = self.get_object()
        today = datetime.date.today()

        if borrowing.actual_return_date:
            return Response(
                {"message": "This book has already been returned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if borrowing.expected_return_date >= today:
            borrowing.return_borrowing()
            return Response(
                {"message": "You have successfully returned the book"},
                status=status.HTTP_200_OK,
            )

        if borrowing.expected_return_date < today:
            fine_payment = borrowing.payments.filter(
                type=Payment.TransactionType.FINE
            ).first()
            if fine_payment:
                if fine_payment.status == Payment.PaymentStatus.PAID:
                    borrowing.return_borrowing()
                    return Response(
                        {"message": "You have successfully returned the book"},
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "message": "You have to pay the fine "
                                       "before returning the book",
                            "payment_url": fine_payment.session_url,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                session_url = create_checkout_session(
                    borrowing, Payment.TransactionType.FINE, request
                )
                return Response(
                    {
                        "message": "You are late! Please pay the "
                                   "fine before returning the book.",
                        "payment_url": session_url,
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
