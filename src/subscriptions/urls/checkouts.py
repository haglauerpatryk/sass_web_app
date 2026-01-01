from django.urls import path

from subscriptions.views import (
    product_price_redirect_view,
    checkout_redirect_view,
    checkout_finalize_view,
)

urlpatterns = [
    path("checkout/sub-price/<int:price_id>/", 
            product_price_redirect_view,
            name='sub-price-checkout'
            ),
    path("checkout/start/", 
            checkout_redirect_view,
            name='stripe-checkout-start'
            ),
    path("checkout/success/", 
            checkout_finalize_view,
            name='stripe-checkout-end'
            ),
]