# Generated by Django 5.2 on 2025-05-02 04:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0013_rename_card_name_payment_razorpay_order_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="payment_method",
            field=models.CharField(default="razorpay", max_length=20),
        ),
    ]
