# Generated by Django 5.0.6 on 2024-10-12 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0009_subscription_subtitle"),
    ]

    operations = [
        migrations.AddField(
            model_name="usersubscription",
            name="cancel_at_period_end",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="current_period_end",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="current_period_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="original_period_start",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("active", "Active"),
                    ("trialing", "Trialing"),
                    ("incomplete", "Incomplete"),
                    ("incomplete_expired", "Incomplete Expired"),
                    ("past_due", "Past Due"),
                    ("canceled", "Canceled"),
                    ("unpaid", "Unpaid"),
                    ("paused", "Paused"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="stripe_id",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="user_cancelled",
            field=models.BooleanField(default=False),
        ),
    ]
