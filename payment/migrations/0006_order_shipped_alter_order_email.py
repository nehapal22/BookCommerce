# Generated by Django 5.2 on 2025-04-25 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payment", "0005_payment"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="shipped",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="order",
            name="email",
            field=models.EmailField(max_length=255),
        ),
    ]
