# Generated by Django 5.2 on 2025-04-19 13:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("borrowings", "0001_initial"),
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="borrowing",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="payments",
                to="borrowings.borrowing",
            ),
        ),
    ]
