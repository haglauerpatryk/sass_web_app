"""
Models for Customer Management.

This module defines the Customer model, which represents user accounts in 
relation to Stripe. It includes fields for managing Stripe customer IDs, 
initial email information, and email confirmation status.

Signals:
    - allauth_user_signed_up_handler: Creates a Customer instance when a user signs up.
    - allauth_email_confirmed_handler: Updates the Customer's email confirmation status 
      upon email verification.
"""

from typing import Any
from django.conf import settings
from django.db import models
from allauth.account.signals import (
    user_signed_up as allauth_user_signed_up,
    email_confirmed as allauth_email_confirmed
)
import helpers.billing
from toolbox.decorators import light_toolbox


User = settings.AUTH_USER_MODEL # "auth.user"

class Customer(models.Model):
    """
    Represents a customer linked to a user account in Stripe.

    Attributes:
        user (User): The user linked to this customer.
        stripe_id (str): The Stripe customer ID for billing purposes.
        init_email (str): Initial email address at signup.
        init_email_confirmed (bool): Tracks whether the initial email was confirmed.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null=True, blank=True)
    init_email = models.EmailField(blank=True, null=True)
    init_email_confirmed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """
        Saves the Customer instance, creating a Stripe customer if necessary.

        If the customer does not have a Stripe ID and has confirmed their email, 
        a new Stripe customer is created, and the Stripe ID is stored.

        Parameters:
            *args: Variable length argument list for overriding save behavior.
            **kwargs: Arbitrary keyword arguments for save customization.
        """
        if not self.stripe_id:
            if self.init_email_confirmed and self.init_email:
                email = self.init_email
                if email != "" or email is not None:
                    stripe_id = helpers.billing.create_customer(email=email,metadata={
                        "user_id": self.user.id, 
                        "username": self.user.username
                    }, raw=False)
                    self.stripe_id = stripe_id
        super().save(*args, **kwargs)
        # post -save will not update
        # self.stripe_id = "something else"
        # self.save()


@light_toolbox
def allauth_user_signed_up_handler(request: Any, user: Any, *args: Any, **kwargs: Any) -> None:
    """
    Signal handler to create a Customer when a user signs up.

    Parameters:
        request (HttpRequest): The HTTP request object during signup.
        user (User): The user instance for whom the Customer will be created.
    """
    email = user.email
    Customer.objects.create(
        user=user,
        init_email=email,
        init_email_confirmed=False,
    )

allauth_user_signed_up.connect(allauth_user_signed_up_handler)


@light_toolbox
def allauth_email_confirmed_handler(request: Any, email_address: Any, *args: Any, **kwargs: Any) -> None:
    """
    Signal handler to update the email confirmation status on the Customer model.

    When a user's email is confirmed, this handler updates the `init_email_confirmed`
    field for any Customer records associated with that email.

    Parameters:
        request (HttpRequest): The HTTP request object during email confirmation.
        email_address (str): The confirmed email address.
    """
    qs = Customer.objects.filter(
        init_email=email_address,
        init_email_confirmed=False,
    )
    # does not send the save method or create the
    # stripe customer
    # qs.update(init_email_confirmed=True)
    for obj in qs:
        obj.init_email_confirmed=True
        # send the signal
        obj.save()


allauth_email_confirmed.connect(allauth_email_confirmed_handler)