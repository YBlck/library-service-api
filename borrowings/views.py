from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    BorrowingListAdminSerializer,
    BorrowingDetailAdminSerializer,
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

        if status:
            queryset = queryset.filter(actual_return_date__isnull=True)

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

        return BorrowingSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
