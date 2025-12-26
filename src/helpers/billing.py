"""
Billing Helpers for Stripe Integration.

This module contains helper functions to interact with Stripe for operations 
related to customers, products, prices, and subscriptions. It includes 
serialization utilities and functions to manage checkout sessions.

Environment Variables:
    - STRIPE_SECRET_KEY: The secret key for accessing Stripe API.
    - DJANGO_DEBUG: Set to True for development mode.
    - STRIPE_TEST_OVERRIDE: Allows using test keys in production if enabled.

Functions:
    - serialize_subscription_data: Serializes a Stripe subscription response.
    - create_customer: Creates a new Stripe customer.
    - create_product: Creates a new Stripe product.
    - create_price: Creates a price for a Stripe product.
    - start_checkout_session: Initiates a Stripe checkout session.
    - get_checkout_session: Retrieves details of a Stripe checkout session.
    - get_subscription: Retrieves a Stripe subscription.
    - get_customer_active_subscriptions: Retrieves active subscriptions for a customer.
    - cancel_subscription: Cancels a Stripe subscription with optional feedback.
    - get_checkout_customer_plan: Retrieves customer plan data from a session ID.
"""

from typing import Optional, Dict, Any
import stripe
from decouple import config
from . import date_utils
from toolbox.decorators import light_toolbox


DJANGO_DEBUG=config("DJANGO_DEBUG", default=False, cast=bool)
STRIPE_SECRET_KEY=config("STRIPE_SECRET_KEY", default="", cast=str)

if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    raise ValueError("Invalid stripe key for prod")

stripe.api_key = STRIPE_SECRET_KEY


@light_toolbox
def serialize_subscription_data(subscription_response: stripe.Subscription) -> Dict[str, Any]:
    """
    Serializes relevant fields from a Stripe subscription object.

    Parameters:
        subscription_response (stripe.Subscription): The Stripe subscription object.

    Returns:
        Dict[str, Any]: Serialized subscription data including status, 
        period start/end dates, and cancellation status.
    """
    status = subscription_response.status
    current_period_start = date_utils.timestamp_as_datetime(subscription_response.current_period_start)
    current_period_end = date_utils.timestamp_as_datetime(subscription_response.current_period_end)
    cancel_at_period_end = subscription_response.cancel_at_period_end
    return {
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "status": status,
        "cancel_at_period_end": cancel_at_period_end,
    }


@light_toolbox
def create_customer(
        name: str = "", 
        email: str = "", 
        metadata: Dict[str, Any] = {},
        raw: bool = False) -> Any:
    """
    Creates a Stripe customer.

    Parameters:
        name (str): Customer's name.
        email (str): Customer's email address.
        metadata (Dict[str, Any]): Additional data to attach to the customer.
        raw (bool): If True, returns the raw Stripe customer object.

    Returns:
        Any: Customer ID as a string if `raw` is False; otherwise, the full Stripe object.
    """
    response = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata,
    )
    if raw:
        return response
    stripe_id = response.id 
    return stripe_id


@light_toolbox
def create_product(
        name: str = "", 
        metadata: Dict[str, Any] = {},
        raw: bool = False) -> Any:
    """
    Creates a Stripe product.

    Parameters:
        name (str): The product name.
        metadata (Dict[str, Any]): Additional data to attach to the product.
        raw (bool): If True, returns the raw Stripe product object.

    Returns:
        Any: Product ID as a string if `raw` is False; otherwise, the full Stripe object.
    """
    response = stripe.Product.create(
        name = name,
        metadata = metadata,
    )
    if raw:
        return response
    stripe_id = response.id 
    return stripe_id


@light_toolbox
def create_price(
        currency: str = "usd",
        unit_amount: int = 9999,
        interval: str = "month",
        product: Optional[str] = None,
        metadata: Dict[str, Any] = {},
        raw: bool = False) -> Optional[Any]:
    """
    Creates a Stripe price for a given product.

    Parameters:
        currency (str): Currency for the price, default is USD.
        unit_amount (int): Amount in the smallest currency unit (e.g., cents).
        interval (str): Billing interval, e.g., 'month' or 'year'.
        product (Optional[str]): The Stripe product ID for the price.
        metadata (Dict[str, Any]): Additional metadata for the price.
        raw (bool): If True, returns the raw Stripe price object.

    Returns:
        Optional[Any]: Price ID as a string if `raw` is False; otherwise, 
        the full Stripe object, or None if no product ID is provided.
    """
    if product is None:
        return None
    response = stripe.Price.create(
            currency=currency,
            unit_amount=unit_amount,
            recurring={"interval": interval},
            product=product,
            metadata=metadata
        )
    if raw:
        return response
    stripe_id = response.id 
    return stripe_id


@light_toolbox
def start_checkout_session(
        customer_id: str, 
        success_url: str = "", 
        cancel_url: str = "", 
        price_stripe_id: str = "", 
        raw: bool = True) -> Any:
    """
    Starts a Stripe checkout session for a subscription.

    Parameters:
        customer_id (str): The Stripe customer ID.
        success_url (str): Redirect URL for successful checkout.
        cancel_url (str): Redirect URL for canceled checkout.
        price_stripe_id (str): The Stripe price ID for the session.
        raw (bool): If True, returns the raw Stripe session object.

    Returns:
        Any: Checkout session URL if `raw` is False; otherwise, the full Stripe session object.
    """
    if not success_url.endswith("?session_id={CHECKOUT_SESSION_ID}"):
        success_url = f"{success_url}" + "?session_id={CHECKOUT_SESSION_ID}"

    response= stripe.checkout.Session.create(
        customer=customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": price_stripe_id, "quantity": 1}],
        mode="subscription",
    )
    if raw:
        return response
    return response.url


@light_toolbox
def get_checkout_session(stripe_id: str, raw: bool = True) -> Any:
    """
    Retrieves a Stripe checkout session.

    Parameters:
        stripe_id (str): The Stripe session ID.
        raw (bool): If True, returns the raw Stripe session object.

    Returns:
        Any: Full Stripe session object if `raw` is True; otherwise, session URL.
    """
    response =  stripe.checkout.Session.retrieve(
            stripe_id
        )
    if raw:
        return response
    return response.url


@light_toolbox
def get_subscription(stripe_id: str, raw: bool = True) -> Any:
    """
    Retrieves a Stripe subscription.

    Parameters:
        stripe_id (str): The Stripe subscription ID.
        raw (bool): If True, returns the raw Stripe subscription object.

    Returns:
        Any: Serialized subscription data if `raw` is False; otherwise, the full Stripe object.
    """
    response =  stripe.Subscription.retrieve(
            stripe_id
        )
    if raw:
        return response
    return serialize_subscription_data(response)


@light_toolbox
def get_customer_active_subscriptions(customer_stripe_id: str) -> Any:
    """
    Retrieves active subscriptions for a given customer in Stripe.

    Parameters:
        customer_stripe_id (str): The Stripe customer ID.

    Returns:
        Any: Active subscriptions for the customer as a Stripe list object.
    """
    response =  stripe.Subscription.list(
            customer=customer_stripe_id,
            status="active"
        )
    return response


@light_toolbox
def cancel_subscription(
        stripe_id: str, 
        reason: str = "", 
        feedback: str = "other", 
        cancel_at_period_end: bool = False, 
        raw: bool = True) -> Any:
    """
    Cancels a Stripe subscription with optional feedback and timing.

    Parameters:
        stripe_id (str): The Stripe subscription ID to cancel.
        reason (str): Cancellation reason.
        feedback (str): Cancellation feedback type.
        cancel_at_period_end (bool): If True, cancels at the end of the billing period.
        raw (bool): If True, returns the raw Stripe subscription object.

    Returns:
        Any: Serialized subscription data if `raw` is False; otherwise, the full Stripe object.
    """
    if cancel_at_period_end:
        response =  stripe.Subscription.modify(
                stripe_id,
                cancel_at_period_end=cancel_at_period_end,
                cancellation_details={
                    "comment": reason,
                    "feedback": feedback
                }
            )
    else:
        response =  stripe.Subscription.cancel(
                stripe_id,
                cancellation_details={
                    "comment": reason,
                    "feedback": feedback
                }
            )
    if raw:
        return response
    return serialize_subscription_data(response)


@light_toolbox
def get_checkout_customer_plan(session_id: str) -> Dict[str, Any]:
    """
    Retrieves a customer's subscription plan details from a checkout session.

    Parameters:
        session_id (str): The Stripe checkout session ID.

    Returns:
        Dict[str, Any]: Serialized subscription data including customer ID, 
        plan ID, and other subscription details.
    """
    checkout_r = get_checkout_session(session_id, raw=True)
    customer_id = checkout_r.customer
    sub_stripe_id = checkout_r.subscription
    sub_r = get_subscription(sub_stripe_id, raw=True)
    # current_period_start
    # current_period_end
    sub_plan = sub_r.plan
    subscription_data = serialize_subscription_data(sub_r)
    data = {
        "customer_id": customer_id,
        "plan_id": sub_plan.id,
        "sub_stripe_id": sub_stripe_id,
       **subscription_data,
    }
    return data
