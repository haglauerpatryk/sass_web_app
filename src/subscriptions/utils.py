"""
Utilities for Subscription Management.

This module contains utility functions for managing and synchronizing user 
subscriptions with Stripe. Functions cover actions such as refreshing active 
subscriptions, clearing inactive or dangling subscriptions, and synchronizing 
group permissions with subscription levels.

Functions:
    - refresh_active_users_subscriptions: Updates user subscriptions based on 
      filters like active status, date range, and user IDs.
    - clear_dangling_subs: Clears inactive or unused subscriptions from Stripe 
      to prevent unwanted charges.
    - sync_subs_group_permissions: Synchronizes permissions for groups 
      associated with active subscriptions.
"""

import helpers.billing
from django.db.models import Q
from customers.models import Customer
from subscriptions.models import Subscription, UserSubscription, SubscriptionStatus

from toolbox.decorators import light_toolbox


@light_toolbox
def refresh_active_users_subscriptions(
        user_ids=None, 
        active_only=True,
        days_left=-1,
        days_ago=-1,
        day_start=-1,
        day_end=-1,
        verbose=False) -> bool:
    """
    Refreshes active user subscriptions based on specified filters.

    This function updates active subscriptions for users by fetching the latest 
    subscription details from Stripe. Filtering options allow narrowing updates 
    to specific user IDs, date ranges, or active subscriptions.

    Parameters:
        user_ids (list[int] | int | None): List of user IDs or a single user ID 
            to filter subscriptions, or None to include all.
        active_only (bool): If True, only refresh active or trialing subscriptions.
        days_left (int): Number of days remaining in subscription to filter by.
        days_ago (int): Number of days ago a subscription started, used for filtering.
        day_start (int): Start day range to filter subscriptions by date range.
        day_end (int): End day range to filter subscriptions by date range.
        verbose (bool): If True, prints progress for each subscription processed.

    Returns:
        bool: True if all subscriptions were successfully updated, False if any 
            updates failed.
    """
    qs = UserSubscription.objects.all()
    if active_only:
        qs = qs.by_active_trialing()
    if user_ids is not None:
        qs = qs.by_user_ids(user_ids=user_ids)
    if days_ago > -1:
        qs = qs.by_days_ago(days_ago=days_ago)
    if days_left > -1:
        qs = qs.by_days_left(days_left=days_left)
    if day_start > -1 and day_end > -1:
        qs = qs.by_range(days_start=day_start, days_end=day_end, verbose=verbose)
    complete_count = 0
    qs_count = qs.count()
    for obj in qs:
        if verbose:
            print("Updating user", obj.user, obj.subscription, obj.current_period_end)
        if obj.stripe_id:
            sub_data = helpers.billing.get_subscription(obj.stripe_id, raw=False)
            for k,v in sub_data.items():
                setattr(obj, k, v)
            obj.save()
            complete_count += 1
    return complete_count == qs_count


@light_toolbox
def clear_dangling_subs() -> None:
    """
    Clears inactive or dangling subscriptions in Stripe.

    This function iterates through all customers with a Stripe ID and removes 
    any active but unused subscriptions from Stripe, ensuring no lingering 
    charges for abandoned subscriptions.

    Raises:
        Exception: If Stripe interaction fails for any subscription cancellation.
    """
    qs = Customer.objects.filter(stripe_id__isnull=False)
    for customer_obj in qs:
        user = customer_obj.user
        customer_stripe_id = customer_obj.stripe_id
        print(f"Sync {user} - {customer_stripe_id} subs and remove old ones")
        subs =  helpers.billing.get_customer_active_subscriptions(customer_stripe_id)
        for sub in subs:
            existing_user_subs_qs = UserSubscription.objects.filter(stripe_id__iexact=f"{sub.id}".strip())
            if existing_user_subs_qs.exists():
                continue
            helpers.billing.cancel_subscription(sub.id, reason="Dangling active subscription", cancel_at_period_end=False)
            # print(sub.id, existing_user_subs_qs.exists())


@light_toolbox
def sync_subs_group_permissions() -> None:
    """
    Synchronizes permissions for groups associated with active subscriptions.

    For each active subscription, the function assigns its specific permissions 
    to all groups linked to it. Ensures that groups accurately reflect 
    subscription levels and access controls.

    Modifies:
        Permissions for each group associated with an active subscription.
    """
    qs = Subscription.objects.filter(active=True)
    for obj in qs:
        sub_perms = obj.permissions.all()
        for group in obj.groups.all():
            group.permissions.set(sub_perms)