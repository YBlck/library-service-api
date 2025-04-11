from django.urls import path, include
from rest_framework.routers import DefaultRouter

from books.views import BookViewSet

app_name = "books"

router = DefaultRouter()
router.register(r"", BookViewSet, basename="book")

urlpatterns = router.urls