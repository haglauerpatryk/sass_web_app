# Generated by Django 5.0.6 on 2024-09-23 17:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0003_subscriptionprice"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="subscriptionprice",
            options={"ordering": ["order", "featured", "-updated"]},
        ),
    ]