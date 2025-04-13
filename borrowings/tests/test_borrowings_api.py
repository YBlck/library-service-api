import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def get_detail_url(borrow_id):
    return reverse("borrowings:borrowing-detail", args=[borrow_id])


class BorrowingsAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = get_user_model().objects.create(
            email="user@test.com", password="1qazcde3"
        )
        cls.test_admin = get_user_model().objects.create(
            email="admin@test.com", password="1qazcde3", is_staff=True
        )
        cls.book_1 = Book.objects.create(
            title="Book_1", author="Author_1", inventory=10, daily_fee=0.50
        )
        cls.book_2 = Book.objects.create(
            title="Book_2", author="Author_2", inventory=10, daily_fee=0.50
        )
        cls.borrowing_1 = Borrowing.objects.create(
            expected_return_date=datetime.date.today()
            + datetime.timedelta(days=3),
            user=cls.test_user,
            book=cls.book_1,
        )
        cls.borrowing_2 = Borrowing.objects.create(
            expected_return_date=datetime.date.today()
            + datetime.timedelta(days=3),
            user=cls.test_admin,
            book=cls.book_2,
        )


class UnauthorizedUserTests(BorrowingsAPITestCase):

    def test_borrowings_list_authorization_required(self):
        response = self.client.get(BORROWINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_borrowings_detail_authorization_required(self):
        url = get_detail_url(self.borrowing_1.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedUserTests(BorrowingsAPITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)

    def test_borrowings_list(self):
        response = self.client.get(BORROWINGS_URL)
        borrowings = Borrowing.objects.filter(user=self.test_user)
        serializer = BorrowingListSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        for borrow in borrowings:
            self.assertEqual(borrow.user, self.test_user)

    def test_borrowings_detail(self):
        url = get_detail_url(self.borrowing_1.id)
        response = self.client.get(url)
        serializer = BorrowingDetailSerializer(self.borrowing_1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_borrowings_detail_of_another_user(self):
        url = get_detail_url(self.borrowing_2.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_borrowing(self):
        book = Book.objects.create(
            title="Test_Book",
            author="Test_Author",
            inventory=10,
            daily_fee=0.50,
        )
        payload = {
            "expected_return_date": datetime.date.today()
            + datetime.timedelta(days=5),
            "book": book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)
        borrowing = Borrowing.objects.get(id=response.data["id"])
        borrowed_book = Book.objects.get(id=borrowing.book.id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(borrowed_book.inventory, book.inventory - 1)
        self.assertEqual(borrowing.user, self.test_user)

    def test_create_forbidden_when_book_inventory_equal_to_zero(self):
        book = Book.objects.create(
            title="Test_Book",
            author="Test_Author",
            inventory=0,
            daily_fee=0.50,
        )
        payload = {
            "expected_return_date": datetime.date.today()
            + datetime.timedelta(days=5),
            "book": book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
