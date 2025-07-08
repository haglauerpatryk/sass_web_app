"""
Views for handling the checkout process.

This module includes views for managing subscription plan redirections,
initiating the Stripe checkout process, and finalizing subscription purchases.

Views:
    - product_price_redirect_view: Redirects to start a checkout session for a specific price.
    - checkout_redirect_view: Starts the Stripe checkout session for a subscription price.
    - checkout_finalize_view: Finalizes the checkout process and updates user subscriptions.
"""
from typing import Optional
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse

import helpers.billing
from subscriptions.models import SubscriptionPrice, Subscription, UserSubscription
from customers.models import Customer
User = get_user_model()
BASE_URL = settings.BASE_URL


def product_price_redirect_view(
        request: HttpRequest, 
        price_id: Optional[int] = None, 
        *args, 
        **kwargs) -> HttpResponse:
    """
    Redirects the user to the Stripe checkout start page for the given subscription price.

    Stores the subscription price ID in the session for later retrieval.

    Parameters:
        request (HttpRequest): The HTTP request object.
        price_id (Optional[int]): The ID of the subscription price.

    Returns:
        HttpResponse: A redirect to the checkout start page.
    """
    request.session['checkout_subscription_price_id'] = price_id
    return redirect("stripe-checkout-start")


@login_required
def checkout_redirect_view(request: HttpRequest) -> HttpResponse:
    """
    Initiates the Stripe checkout session for a selected subscription price.

    Retrieves the subscription price ID from the session and starts the checkout 
    process using Stripe. If the subscription price is not found, redirects to the pricing page.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A redirect to the Stripe checkout session or the pricing page.
    """
    price_id = request.session.get("checkout_subscription_price_id")
    if price_id is None:
        return redirect("pricing")
    price_obj = SubscriptionPrice.objects.filter(id=price_id).first()
    if price_obj is None:
        return redirect("pricing")
    
    customer = getattr(request.user, "customer", None)
    if customer is None or not customer.stripe_id:
        stripe_customer_id = helpers.billing.create_customer(request.user)
        customer = Customer.objects.create(user=request.user, stripe_id=stripe_customer_id)
    customer_stripe_id = customer.stripe_id
    success_url = request.build_absolute_uri(reverse('stripe-checkout-end'))
    cancel_url = request.build_absolute_uri(reverse('pricing'))

    url = helpers.billing.start_checkout_session(
        customer_stripe_id,
        success_url=success_url,
        cancel_url=cancel_url,
        price_stripe_id=price_obj.stripe_id,
        raw=False

    )
    return redirect(url)


def checkout_finalize_view(request: HttpRequest) -> HttpResponse:
    """
    Finalizes the checkout process and updates the user's subscription.

    Handles the Stripe checkout session to retrieve the subscription details 
    and updates the user's subscription status. If errors occur (e.g., missing
    subscription or user), returns a bad request response.

    Parameters:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: A success message or an HTTP 400 Bad Request if errors occur.
    """
    session_id = request.GET.get('session_id')
    if not session_id:
        return HttpResponseBadRequest("Missing session ID.")
    
    checkout_data = helpers.billing.get_checkout_customer_plan(session_id)
    plan_id = checkout_data.pop('plan_id', None)
    customer_id = checkout_data.pop('customer_id', None)
    sub_stripe_id = checkout_data.pop("sub_stripe_id", None)

    if not all([plan_id, customer_id, sub_stripe_id]):
        return HttpResponseBadRequest("Invalid checkout data.")
    
    try:
        sub_obj = Subscription.objects.get(subscriptionprice__stripe_id=plan_id)
    except Subscription.DoesNotExist:
        return HttpResponseBadRequest("Invalid subscription ID.")
    try:
        user_obj = User.objects.get(customer__stripe_id=customer_id)
    except User.DoesNotExist:
        return HttpResponseBadRequest("Invalid customer ID.")

    updated_sub_options = {
        "subscription": sub_obj,
        "stripe_id": sub_stripe_id,
        "user_cancelled": False,
        **checkout_data
    }

    _user_sub_obj, created = UserSubscription.objects.get_or_create(
        user=user_obj, defaults=updated_sub_options
    )
    if not created:
        old_stripe_id = _user_sub_obj.stripe_id
        if old_stripe_id and old_stripe_id != sub_stripe_id:
            try:
                helpers.billing.cancel_subscription(old_stripe_id, reason="Auto ended, new membership", feedback="other")
            except Exception:
                pass
        for k, v in updated_sub_options.items():
            setattr(_user_sub_obj, k, v)
        _user_sub_obj.save()

        messages.success(request, "Success! Thank you for joining.")
        return redirect(_user_sub_obj.get_absolute_url())
    return render(request, "checkout/success.html", {})