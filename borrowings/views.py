import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
        if borrowing.actual_return_date:
            return Response(
                {"message": "This book has already been returned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = datetime.date.today()
        borrowing.book.increase_inventory()
        borrowing.save()
        return Response(
            {"message": "You have successfully returned the book"},
            status=status.HTTP_200_OK,
        )
