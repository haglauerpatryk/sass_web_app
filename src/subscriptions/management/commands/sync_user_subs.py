"""
Management Command: sync_user_subs

Synchronizes user subscriptions by updating active subscriptions or clearing 
inactive, dangling subscriptions in Stripe.

Usage:
    python manage.py sync_user_subs [options]

Options:
    --day-start (int): Start day range for filtering subscriptions.
    --day-end (int): End day range for filtering subscriptions.
    --days-left (int): Days left in the subscription period.
    --days-ago (int): Days since subscription started.
    --clear-dangling (bool): Flag to clear inactive subscriptions on Stripe.
"""

import logging
from typing import Any
from django.core.management.base import BaseCommand, CommandError
from subscriptions import utils as subs_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Command(BaseCommand):
    """
    Syncs user subscriptions based on provided filters and options.
    
    Uses `refresh_active_users_subscriptions` for updating active subscriptions 
    or `clear_dangling_subs` to remove inactive, dangling subscriptions in Stripe.
    """

    def add_arguments(self, parser):
        parser.add_argument("--day-start", default=0, type=int, help="Start day range for subscription filtering.")
        parser.add_argument("--day-end", default=0, type=int, help="End day range for subscription filtering.")
        parser.add_argument("--days-left", default=0, type=int, help="Days left in the subscription period.")
        parser.add_argument("--days-ago", default=0, type=int, help="Days since subscription started.")
        parser.add_argument("--clear-dangling", action="store_true", help="Clear inactive subscriptions in Stripe.")

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Runs the subscription sync process based on options.

        Syncs active user subscriptions or clears dangling subscriptions 
        in Stripe based on the specified arguments. Handles errors gracefully.
        """
        try:
            if options["clear_dangling"]:
                self.stdout.write("Clearing inactive Stripe subscriptions...")
                logger.info("Clearing inactive Stripe subscriptions.")
                subs_utils.clear_dangling_subs()
                self.stdout.write(self.style.SUCCESS("Cleared inactive subscriptions successfully."))
            else:
                self.stdout.write("Synchronizing active user subscriptions...")
                logger.info("Starting active user subscription synchronization.")
                result = subs_utils.refresh_active_users_subscriptions(
                    active_only=True, 
                    days_left=options["days_left"],
                    days_ago=options["days_ago"],
                    day_start=options["day_start"],
                    day_end=options["day_end"],
                    verbose=True
                )
                if result:
                    self.stdout.write(self.style.SUCCESS("Subscription synchronization completed."))
                    logger.info("Subscription synchronization completed successfully.")
                else:
                    self.stdout.write(self.style.ERROR("Some subscriptions failed to synchronize."))
                    logger.warning("Subscription synchronization encountered issues.")
        
        except Exception as e:
            error_msg = f"Error in subscription synchronization: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise CommandError("Subscription synchronization failed.") from e
