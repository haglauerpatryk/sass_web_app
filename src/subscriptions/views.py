"""
Views for Subscription Management.

This module provides views for user subscription management, including 
viewing subscription details, canceling subscriptions, and listing available 
subscription plans. Each view function uses Django’s authentication system 
to ensure access control.

Views:
    - user_subscription_view: Displays and refreshes the user’s subscription details.
    - user_subscription_cancel_view: Allows users to cancel their subscription.
    - subscription_price_view: Lists available subscription prices with monthly 
      and yearly filtering options.
"""

import logging
from typing import Optional
import helpers.billing
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from subscriptions.models import SubscriptionPrice, UserSubscription
from subscriptions import utils as subs_utils

from toolbox.decorators import light_toolbox

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@light_toolbox
@login_required
def user_subscription_view(request: HttpRequest) -> HttpResponse:
    """
    Display and refresh the user's subscription details.

    This view allows authenticated users to view their current subscription 
    details and, if needed, refresh the subscription to ensure accurate 
    information is displayed.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders the user's subscription detail template.
    """
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    if request.method == "POST":
        print("refresh sub")
        finished = subs_utils.refresh_active_users_subscriptions(user_ids=[request.user.id], active_only=False)
        if finished:
            messages.success(request, "Your plan details have been refreshed.")
        else:
            messages.error(request, "Your plan details have not been refreshed, please try again.")
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_detail_view.html', {"subscription": user_sub_obj})


@light_toolbox
@login_required
def user_subscription_cancel_view(request: HttpRequest) -> HttpResponse:
    """
    Allow a user to cancel their active subscription.

    If the user has an active subscription, this view processes the cancellation 
    in Stripe and updates the subscription status. The cancellation may be set 
    to take effect at the end of the billing period.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Redirects to the user's subscription details page on success; 
            otherwise, renders the cancel confirmation template.
    """
    user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
    if request.method == "POST":
        if user_sub_obj.stripe_id and user_sub_obj.is_active_status:
            sub_data = helpers.billing.cancel_subscription(
                user_sub_obj.stripe_id, 
                reason="User wanted to end", 
                feedback="other",
                cancel_at_period_end=True,
                raw=False)
            for k,v in sub_data.items():
                setattr(user_sub_obj, k, v)
            user_sub_obj.save()
            messages.success(request, "Your plan has been cancelled.")
        return redirect(user_sub_obj.get_absolute_url())
    return render(request, 'subscriptions/user_cancel_view.html', {"subscription": user_sub_obj})


@light_toolbox
def subscription_price_view(
        request: HttpRequest, 
        interval: Optional[str] = "month") -> HttpResponse:
    """
    List available subscription prices with monthly and yearly options.

    This view displays featured subscription plans filtered by the specified 
    billing interval (monthly or yearly), allowing users to view different 
    subscription options and choose a plan that fits their needs.

    Parameters:
        request (HttpRequest): The HTTP request object.
        interval (str): The billing interval for the plans ('month' or 'year').

    Returns:
        HttpResponse: Renders the subscription pricing template with filtered plans.
    """
    qs = SubscriptionPrice.objects.filter(featured=True)
    inv_mo = SubscriptionPrice.IntervalChoices.MONTHLY
    inv_yr = SubscriptionPrice.IntervalChoices.YEARLY
    object_list = qs.filter(interval=inv_mo)
    url_path_name = "pricing_interval"
    mo_url = reverse(url_path_name, kwargs={"interval": inv_mo})
    yr_url = reverse(url_path_name, kwargs={"interval": inv_yr})
    active = inv_mo
    if interval == inv_yr:
        active = inv_yr
        object_list = qs.filter(interval=inv_yr)
    return render(request, "subscriptions/pricing.html", {
        "object_list": object_list,
        "mo_url": mo_url,
        "yr_url": yr_url,
        "active": active,
    })