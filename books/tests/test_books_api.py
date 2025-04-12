from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer

BOOKS_URL = reverse("books:book-list")


def get_detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])


def create_book(**params):
    defaults = {
        "title": "Sample book",
        "author": "Sample author",
        "inventory": 10,
        "daily_fee": 0.50,
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class BooksAPITestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_user = get_user_model().objects.create(
            email="user@test.com", password="1qazcde3"
        )
        cls.test_admin = get_user_model().objects.create(
            email="admin@test.com", password="1qazcde3", is_staff=True
        )
        for i in range(5):
            Book.objects.create(
                title=f"Book_{i}",
                author=f"Author_{i}",
                inventory=10,
                daily_fee=0.50,
            )


class UnauthorizedUserTests(BooksAPITestCase):
    def test_books_list(self):
        response = self.client.get(BOOKS_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, serializer.data)

    def test_books_detail(self):
        book = Book.objects.first()
        response = self.client.get(get_detail_url(book.id))
        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, serializer.data)

    def test_book_create_forbidden(self):
        payload = {
            "title": "Test title",
            "author": "Test author",
            "inventory": 10,
            "daily_fee": 0.50,
        }
        response = self.client.post(BOOKS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_book_update_forbidden(self):
        book = create_book()
        payload = {
            "title": "Test title",
            "author": "Test author",
            "inventory": 10,
            "daily_fee": 0.50,
        }
        response = self.client.put(get_detail_url(book.id), payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_book_delete_forbidden(self):
        book = create_book()
        response = self.client.delete(get_detail_url(book.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedUserTests(BooksAPITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)

    def test_books_list(self):
        response = self.client.get(BOOKS_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, serializer.data)

    def test_books_detail(self):
        book = Book.objects.first()
        response = self.client.get(get_detail_url(book.id))
        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, serializer.data)

    def test_book_create_forbidden(self):
        payload = {
            "title": "Test title",
            "author": "Test author",
            "inventory": 10,
            "daily_fee": 0.50,
        }
        response = self.client.post(BOOKS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_update_forbidden(self):
        book = create_book()
        payload = {
            "title": "Test title",
            "author": "Test author",
            "inventory": 10,
            "daily_fee": 0.50,
        }
        response = self.client.put(get_detail_url(book.id), payload)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_book_delete_forbidden(self):
        book = create_book()
        response = self.client.delete(get_detail_url(book.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminUserTests(BooksAPITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_admin)

    def test_books_list(self):
        response = self.client.get(BOOKS_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, serializer.data)

    def test_books_detail(self):
        book = Book.objects.first()
        response = self.client.get(get_detail_url(book.id))
        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, serializer.data)

    def test_book_create_allowed(self):
        payload = {
            "title": "Test title",
            "author": "Test author",
            "inventory": 10,
            "daily_fee": 0.50,
        }
        response = self.client.post(BOOKS_URL, payload)
        book = Book.objects.get(id=response.data["id"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for key in payload:
            self.assertEqual(payload[key], getattr(book, key))

    def test_book_update_allowed(self):
        book = create_book()
        payload = {
            "title": "Test title",
            "author": "Test author",
            "inventory": 10,
            "daily_fee": 0.50,
        }
        response = self.client.put(get_detail_url(book.id), payload)
        updated_book = Book.objects.get(id=book.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in payload:
            self.assertEqual(payload[key], getattr(updated_book, key))

    def test_book_delete_allowed(self):
        book = create_book()
        response = self.client.delete(get_detail_url(book.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
