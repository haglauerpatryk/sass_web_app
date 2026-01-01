from .subscriptions import urlpatterns as subscription_urls
from .checkouts import urlpatterns as checkout_urls

urlpatterns = subscription_urls + checkout_urls