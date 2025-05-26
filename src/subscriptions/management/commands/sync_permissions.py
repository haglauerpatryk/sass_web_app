"""
Management Command: sync_permissions

Synchronizes permissions for groups linked to active subscriptions, 
ensuring each group is assigned the correct permissions.

Usage:
    python manage.py sync_permissions

Dependencies:
    - sync_subs_group_permissions (in subscriptions.utils)
"""

from typing import Any
from django.core.management.base import BaseCommand, CommandError
import logging
from subscriptions import utils as subs_utils

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Command(BaseCommand):
    """
    Sync permissions for groups linked to active subscriptions.

    This command ensures that all groups associated with active 
    subscriptions have the correct permissions by using the 
    `sync_subs_group_permissions` utility function.
    """
    
    help = "Sync permissions for groups linked to active subscriptions."

    def handle(self, *args: Any, **options: Any) -> None:
        """Runs the permissions sync process with error handling."""
        
        self.stdout.write("Starting permissions sync...")
        logger.info("Permissions sync command started.")

        try:
            subs_utils.sync_subs_group_permissions()
            self.stdout.write(self.style.SUCCESS("Permissions sync completed."))
            logger.info("Permissions sync completed successfully.")
        
        except Exception as e:
            error_msg = f"Error in permissions sync: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg)
            raise CommandError("Permissions sync failed.") from e
