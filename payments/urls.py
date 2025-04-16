from django.urls import path, include
from rest_framework.routers import DefaultRouter

from payments.views import PaymentsViewSet

app_name = "payments"


router = DefaultRouter()
router.register("", PaymentsViewSet, basename="payment")

urlpatterns = [
    path("", include(router.urls)),
]
