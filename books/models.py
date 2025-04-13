from django.db import models
from django.db.models import F
from rest_framework.exceptions import ValidationError


class Book(models.Model):
    class CoverType(models.TextChoices):
        HARD = "HARD", "Hardcover"
        SOFT = "SOFT", "Softcover"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(
        max_length=4, choices=CoverType, default=CoverType.HARD
    )
    inventory = models.IntegerField()
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} (author: {self.author}, inventory: {self.inventory})"

    def reduce_inventory(self):
        if self.inventory > 0:
            Book.objects.filter(pk=self.pk).update(
                inventory=F("inventory") - 1
            )
            self.refresh_from_db()
        else:
            raise ValidationError("This book is out of stock")

    def increase_inventory(self):
        Book.objects.filter(pk=self.pk).update(inventory=F("inventory") + 1)
