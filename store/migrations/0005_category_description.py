# Generated by Django 5.2 on 2025-04-18 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0004_customer_user_delete_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="description",
            field=models.TextField(blank=True, null=True),
        ),
    ]
