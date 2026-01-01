
from django.urls import path

from profiles.views.views import profile_list_view, profile_detail_view

urlpatterns = [
    path("", profile_list_view),
    path("<str:username>/", profile_detail_view),
]