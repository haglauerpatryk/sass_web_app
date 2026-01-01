# subscriptions/urls.py

from django.urls import path
from subscriptions.views import subscription_price_view, user_subscription_view, user_subscription_cancel_view

urlpatterns = [
    path("pricing/", subscription_price_view, name='pricing'),
    path("pricing/<str:interval>/", subscription_price_view, name='pricing_interval'),
    path('accounts/billing/', user_subscription_view, name='user_subscription'),
    path('accounts/billing/cancel', user_subscription_cancel_view, name='user_subscription_cancel'),
]