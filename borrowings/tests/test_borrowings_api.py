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
    BorrowingListAdminSerializer,
)

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def get_detail_url(borrow_id):
    return reverse("borrowings:borrowing-detail", args=[borrow_id])


def book_sample(**params):
    defaults = {
        "title": "Test_Book",
        "author": "Test_Author",
        "inventory": 10,
        "daily_fee": 0.50,
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def return_day_sample():
    return datetime.date.today() + datetime.timedelta(days=5)


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
            expected_return_date=return_day_sample(),
            user=cls.test_user,
            book=cls.book_1,
        )
        cls.borrowing_2 = Borrowing.objects.create(
            expected_return_date=return_day_sample(),
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
        book = book_sample()
        payload = {
            "expected_return_date": return_day_sample(),
            "book": book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)
        borrowing = Borrowing.objects.get(id=response.data["borrowing"]["id"])
        borrowed_book = Book.objects.get(id=borrowing.book.id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(borrowed_book.inventory, book.inventory - 1)
        self.assertEqual(borrowing.user, self.test_user)

    def test_create_forbidden_when_book_inventory_equal_to_zero(self):
        book = book_sample(inventory=0)
        payload = {
            "expected_return_date": return_day_sample(),
            "book": book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_borrowings_return(self):
        book = book_sample()
        borrowing = Borrowing.objects.create(
            expected_return_date=return_day_sample(),
            book=book,
            user=self.test_user,
        )
        url = f"{BORROWINGS_URL}{borrowing.id}/return/"
        response = self.client.post(url, data=None)
        updated_borrowing = Borrowing.objects.get(id=borrowing.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            updated_borrowing.actual_return_date, datetime.date.today()
        )
        self.assertEqual(updated_borrowing.book.inventory, book.inventory + 1)

    def test_borrowings_return_twice_forbidden(self):
        book = book_sample()
        borrowing = Borrowing.objects.create(
            expected_return_date=return_day_sample(),
            actual_return_date=datetime.date.today(),
            book=book,
            user=self.test_user,
        )
        url = f"{BORROWINGS_URL}{borrowing.id}/return/"
        response = self.client.post(url, data=None)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AdminUserTests(BorrowingsAPITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_admin)

    def test_borrowings_list(self):
        response = self.client.get(BORROWINGS_URL)
        borrowings = Borrowing.objects.all()
        serializer = BorrowingListAdminSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), borrowings.count())

    def test_borrowings_filter_by_user_id(self):
        response = self.client.get(
            BORROWINGS_URL, data={"user_id": self.test_user.id}
        )
        borrowings = Borrowing.objects.filter(user=self.test_user)
        serializer = BorrowingListAdminSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), borrowings.count())

    def test_borrowings_filter_by_is_active_status(self):
        book = book_sample()
        borrowing = Borrowing.objects.create(
            expected_return_date=return_day_sample(),
            user=self.test_user,
            book=book,
        )
        borrowing.actual_return_date = datetime.date.today()
        response = self.client.get(BORROWINGS_URL, data={"is_active": True})
        borrowings = Borrowing.objects.filter(actual_return_date__isnull=True)
        serializer = BorrowingListAdminSerializer(borrowings, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), borrowings.count())
