from decimal import Decimal

import stripe
from django.conf import settings
from django.http import HttpRequest
from rest_framework.reverse import reverse

from borrowings.models import Borrowing
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(borrowing, transaction_type, request: HttpRequest):
    amount = _calculate_amount(borrowing, transaction_type)
    try:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{transaction_type} for {borrowing.book.title}",
                        },
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=(
                reverse("payments:payment-success")
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),  # build_absolute_uri not work here with stripe because of coding {} symbols
            cancel_url=request.build_absolute_uri(
                reverse("payments:payment-cancel")
            ),
            metadata={
                "borrowing_id": borrowing.id,
                "transaction_type": transaction_type,
            },
        )
    except Exception as e:
        return str(e)

    payment = Payment.objects.create(
        status=Payment.PaymentStatus.PENDING,
        type=transaction_type,
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=amount,
    )

    return session.url


def _calculate_amount(borrowing: Borrowing, transaction_type) -> Decimal:
    if transaction_type == Payment.TransactionType.PAYMENT:
        price = Decimal(borrowing.book.daily_fee)
        return price * borrowing.get_duration_days()
    elif transaction_type == Payment.TransactionType.FINE:
        price = (
            Decimal(borrowing.book.daily_fee) * 2
        )  # later maybe need to move multiplier into variable
        return price * borrowing.get_overdue_days()
    else:
        raise ValueError(f"Invalid transaction type: {transaction_type}")
