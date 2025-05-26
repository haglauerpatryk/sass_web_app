"""
Models and utilities for subscription management, integrating with Stripe 
and Django's permissions framework.

Models:
    Subscription: Represents a subscription plan linked to a Stripe product, 
        associating user groups and permissions with each plan.
        
    SubscriptionPrice: Defines pricing details for a subscription plan, 
        linked to Stripe prices and supporting multiple intervals.
        
    UserSubscription: Tracks individual users' subscription details, 
        including billing periods and status, with Stripe integration.

Enums:
    SubscriptionStatus: Enum representing possible states of a user subscription, 
        such as 'active', 'trialing', 'canceled', and more.

Custom QuerySets:
    UserSubscriptionQuerySet: Provides custom filters for UserSubscription,
        including date-based filtering, active status checks, and user ID filtering.

Managers:
    UserSubscriptionManager: Custom manager using UserSubscriptionQuerySet 
        to enable specialized queries on UserSubscription instances.

Signal Functions:
    user_sub_post_save: Signal handler to update user group memberships 
        based on subscription changes, triggered when UserSubscription instances are saved.
"""

import datetime
from typing import Optional, List, Dict, Union, Any
import helpers.billing
from django.db import models
from django.db.models import Q, QuerySet
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save
from django.conf import settings 
from django.urls import reverse
from django.utils import timezone

from toolbox.decorators import light_toolbox

User = settings.AUTH_USER_MODEL # "auth.User"

ALLOW_CUSTOM_GROUPS: bool = True
SUBSCRIPTION_PERMISSIONS: List[tuple] = [
    ("advanced", "Advanced Perm"),
    ("pro", "Pro Perm"),
    ("basic", "Basic Perm"),
    ("basic_ai", "Basic AI Perm")
]

class Subscription(models.Model):
    """
    Represents a subscription plan associated with a Stripe product.

    Attributes:
        name (str): Name of the subscription plan.
        subtitle (str, optional): Additional description of the plan.
        active (bool): Indicates if the subscription plan is active.
        groups (ManyToMany[Group]): User groups associated with this subscription.
        permissions (ManyToMany[Permission]): Permissions associated with this subscription.
        stripe_id (str): Stripe product ID.
        order (int): Ordering for display on the pricing page.
        featured (bool): Whether the plan is featured on the pricing page.
        updated (datetime): Timestamp for last update.
        timestamp (datetime): Timestamp for when the subscription was created.
        features (str, optional): List of features for display, separated by newline characters.
    """
    name = models.CharField(max_length=120)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group) # one-to-one
    permissions =  models.ManyToManyField(
        Permission, limit_choices_to={
        "content_type__app_label": "subscriptions", 
        "codename__in": [x[0]for x in SUBSCRIPTION_PERMISSIONS]
        }
    )
    stripe_id = models.CharField(max_length=120, null=True, blank=True)

    order = models.IntegerField(default=-1, help_text='Ordering on Django pricing page')
    featured = models.BooleanField(default=True, help_text='Featured on Django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    features = models.TextField(help_text="Features for pricing, seperated by new line", blank=True, null=True)

    class Meta:
        ordering = ['order', 'featured', '-updated']
        permissions = SUBSCRIPTION_PERMISSIONS

    def __str__(self) -> str:
        return f"{self.name}"

    def get_features_as_list(self) -> List[str]:
        """
        Returns the features as a list of strings.
        """
        if not self.features:
            return []
        return [x.strip() for x in self.features.split("\n")]

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overrides save to create a Stripe product ID if missing.
        """
        if not self.stripe_id:
            stripe_id: str = helpers.billing.create_product(
                    name=self.name, 
                    metadata={
                        "subscription_plan_id": self.id
                    }, 
                    raw=False
                )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)


class SubscriptionPrice(models.Model):
    """
    Stores the pricing details for a subscription, linked to a Stripe price.

    Attributes:
        subscription (ForeignKey): Related Subscription plan.
        stripe_id (str): Stripe price ID.
        interval (str): Billing interval, e.g., 'month' or 'year'.
        price (Decimal): Price amount for the subscription.
        order (int): Ordering for display on the pricing page.
        featured (bool): If this price option is featured.
        updated (datetime): Timestamp for last update.
        timestamp (datetime): Timestamp for when the price was created.
    """

    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        YEARLY = "year", "Yearly"

    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    interval = models.CharField(max_length=120, 
                                default=IntervalChoices.MONTHLY, 
                                choices=IntervalChoices.choices
                            )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)
    order = models.IntegerField(default=-1, help_text='Ordering on Django pricing page')
    featured = models.BooleanField(default=True, help_text='Featured on Django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subscription__order', 'order', 'featured', '-updated']

    def get_checkout_url(self) -> str:
        """
        Generates the URL for the checkout page for this price.
        """
        return reverse("sub-price-checkout", 
            kwargs = {"price_id": self.id}  
            )

    @property
    def display_features_list(self) -> List[str]:
        """
        Returns the subscription features as a list of strings.
        """
        if not self.subscription:
            return []
        return self.subscription.get_features_as_list()
    
    @property
    def display_sub_name(self) -> str:
        """
        Returns the subscription plan name.
        """
        if not self.subscription:
            return "Plan"
        return self.subscription.name

    @property
    def display_sub_subtitle(self) -> Optional[str]:
        """
        Returns the subscription plan subtitle.
        """
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle
    
    @property
    def stripe_currency(self) -> str:
        """
        Returns the currency for the price (default: 'usd').
        """
        return "usd"
    
    @property
    def stripe_price(self) -> int:
        """
        Converts the price to cents for Stripe compatibility.
        """
        return int(self.price * 100)

    @property
    def product_stripe_id(self) -> Optional[str]:
        """
        Returns the Stripe product ID associated with the subscription.
        """
        if not self.subscription:
            return None
        return self.subscription.stripe_id
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overrides save to create a Stripe price ID if missing.
        """
        if (not self.stripe_id and 
            self.product_stripe_id is not None):
            stripe_id: str = helpers.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                product=self.product_stripe_id,
                metadata={
                        "subscription_plan_price_id": self.id
                },
                raw=False
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)
        if self.featured and self.subscription:
            qs = SubscriptionPrice.objects.filter(
                subscription=self.subscription,
                interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)

class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    TRIALING = 'trialing', 'Trialing'
    INCOMPLETE = 'incomplete', 'Incomplete'
    INCOMPLETE_EXPIRED = 'incomplete_expired', 'Incomplete Expired'
    PAST_DUE = 'past_due', 'Past Due'
    CANCELED = 'canceled', 'Canceled'
    UNPAID = 'unpaid', 'Unpaid'
    PAUSED = 'paused', 'Paused'

class UserSubscriptionQuerySet(models.QuerySet):
    def by_range(self, 
                 days_start: int = 7, 
                 days_end: int = 120, 
                 verbose: bool = True) -> QuerySet:
        """
        Filters subscriptions by a range of days remaining until expiration.
        """
        now = timezone.now()
        days_start_from_now = now + datetime.timedelta(days=days_start)
        days_end_from_now = now + datetime.timedelta(days=days_end)
        range_start = days_start_from_now.replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = days_end_from_now.replace(hour=23, minute=59, second=59, microsecond=59)
        if verbose:
            print(f"Range is {range_start} to {range_end}")
        return self.filter(
            current_period_end__gte=range_start,
            current_period_end__lte=range_end
        )
    
    def by_days_left(self, days_left: int = 7) -> QuerySet:
        """
        Filters subscriptions that expire in a specific number of days.
        """
        now = timezone.now()
        in_n_days = now + datetime.timedelta(days=days_left)
        day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end
        )
    
    def by_days_ago(self, days_ago: int = 3) -> QuerySet:
        """
        Filters subscriptions that expired a specific number of days ago.
        """
        now = timezone.now()
        in_n_days = now - datetime.timedelta(days=days_ago)
        day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end
        )

    def by_active_trialing(self) -> QuerySet:
        """
        Filters subscriptions that are either active or in a trialing state.
        """
        active_qs_lookup = (
            Q(status = SubscriptionStatus.ACTIVE) |
            Q(status = SubscriptionStatus.TRIALING)
        )
        return self.filter(active_qs_lookup)
    
    def by_user_ids(self, user_ids: Optional[Union[List[int], int, str]] = None) -> QuerySet:
        """
        Filters subscriptions by a list or single instance of user IDs.
        """
        qs = self
        if isinstance(user_ids, list):
            qs = self.filter(user_id__in=user_ids)
        elif isinstance(user_ids, int):
            qs = self.filter(user_id__in=[user_ids])
        elif isinstance(user_ids, str):
            qs = self.filter(user_id__in=[user_ids])
        return qs


class UserSubscriptionManager(models.Manager):
    def get_queryset(self) -> UserSubscriptionQuerySet:
        return UserSubscriptionQuerySet(self.model, using=self._db)

    # def by_user_ids(self, user_ids=None):
    #     return self.get_queryset().by_user_ids(user_ids=user_ids)
        

class UserSubscription(models.Model):
    """
    Represents a subscription associated with a user, including current status 
    and Stripe integration details.

    Attributes:
        user (User): The user holding the subscription.
        subscription (Subscription): The associated subscription plan.
        stripe_id (str): Stripe subscription ID.
        active (bool): Indicates if the subscription is active.
        user_cancelled (bool): Indicates if the user has canceled the subscription.
        current_period_start (datetime): Start date of the current billing period.
        current_period_end (datetime): End date of the current billing period.
        cancel_at_period_end (bool): Indicates if the subscription will end at the period's end.
        status (str): Status of the subscription.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    active = models.BooleanField(default=True)
    user_cancelled = models.BooleanField(default=False)
    original_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_start = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    current_period_end = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, null=True, blank=True)

    objects = UserSubscriptionManager()

    def get_absolute_url(self) -> str:
        """
        Returns the URL for the user's subscription details.
        """
        return reverse("user_subscription")
    
    def get_cancel_url(self) -> str:
        """
        Returns the URL for canceling the subscription.
        """
        return reverse("user_subscription_cancel")
    
    @property
    def is_active_status(self) -> bool:
        """
        Returns True if the subscription is active or trialing.
        """
        return self.status in [
            SubscriptionStatus.ACTIVE, 
            SubscriptionStatus.TRIALING
        ]
    
    @property
    def plan_name(self) -> Optional[str]:
        """
        Returns the subscription plan name.
        """
        if not self.subscription:
            return None
        return self.subscription.name

    def serialize(self) -> Dict[str, Optional[Union[str, datetime.datetime]]]:
        """
        Serializes the subscription details to a dictionary.
        """
        return {
            "plan_name": self.plan_name,
            "status": self.status,
            "current_period_start": self.current_period_start,
            "current_period_end": self.current_period_end,
        }

    @property
    def billing_cycle_anchor(self) -> Optional[int]:
        """
        Calculates the billing cycle anchor as a Unix timestamp, used for delayed 
        subscription start in Stripe.

        https://docs.stripe.com/payments/checkout/billing-cycle
        Optional delay to start new subscription in
        Stripe checkout
        """
        if not self.current_period_end:
            return None
        return int(self.current_period_end.timestamp())

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Overrides save to set original period start if not set.
        """
        if (self.original_period_start is None and
            self.current_period_start is not None
            ):
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)


@light_toolbox
def user_sub_post_save(
        sender: models.Model, 
        instance: UserSubscription, 
        *args: Any, 
        **kwargs: Any) -> None:
    """
    Signal handler to update user's group memberships based on their subscription plan.
    """
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = Subscription.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list("groups__id", flat=True)
        subs_groups_set = set(subs_groups)
        # groups_ids = groups.values_list('id', flat=True) # [1, 2, 3] 
        current_groups = user.groups.all().values_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - subs_groups_set
        final_group_ids = list(groups_ids_set | current_groups_set)
        user.groups.set(final_group_ids)


post_save.connect(user_sub_post_save, sender=UserSubscription)