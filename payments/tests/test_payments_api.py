import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment
from payments.serializers import PaymentListSerializer, PaymentDetailSerializer

PAYMENT_URL = reverse("payments:payment-list")


def get_detail_url(payment_id):
    return reverse("payments:payment-detail", args=[payment_id])


def return_day_sample():
    return datetime.date.today() + datetime.timedelta(days=5)


class PaymentsAPITestCase(TestCase):
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
        cls.payment_1 = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowing=cls.borrowing_1,
            session_url="https://example.com",
            session_id="session_id_1",
            money_to_pay=10,
        )
        cls.payment_2 = Payment.objects.create(
            status="PENDING",
            type="PAYMENT",
            borrowing=cls.borrowing_2,
            session_url="https://example.com",
            session_id="session_id_2",
            money_to_pay=10,
        )


class UnauthorizedUserTests(PaymentsAPITestCase):

    def test_payments_list_authorization_required(self):
        response = self.client.get(PAYMENT_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payments_detail_authorization_required(self):
        response = self.client.get(get_detail_url(self.payment_1.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorizedUserTests(PaymentsAPITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)

    def test_payments_list(self):
        response = self.client.get(PAYMENT_URL)
        payments = Payment.objects.filter(
            borrowing__user__id=self.test_user.id
        )
        serializer = PaymentListSerializer(payments, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(payments.count(), len(serializer.data))
        for payment in payments:
            self.assertEqual(payment.borrowing.user.id, self.test_user.id)

    def test_payment_detail_with_correct_user(self):
        response = self.client.get(get_detail_url(self.payment_1.id))
        payment = Payment.objects.get(id=response.data["id"])
        serializer = PaymentDetailSerializer(payment)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_payment_detail_with_incorrect_user(self):
        response = self.client.get(get_detail_url(self.payment_2.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminUserTests(PaymentsAPITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_admin)

    def test_payments_list(self):
        response = self.client.get(PAYMENT_URL)
        payments = Payment.objects.all()
        serializer = PaymentListSerializer(payments, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(payments.count(), len(serializer.data))
