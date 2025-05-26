from typing import Optional
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.contrib.auth import get_user_model

from toolbox.decorators import light_toolbox

User = get_user_model()


@light_toolbox
@login_required
def profile_list_view(request: HttpRequest) -> HttpResponse:
    """
    Displays a list of active user profiles.

    Requires the user to be logged in. Filters the user list to include
    only active users for display.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTML response displaying a list of active user profiles.
    """
    context = {
        "object_list": User.objects.filter(is_active=True)
    }
    return render(request, "profiles/list.html", context)


@light_toolbox
@login_required
def profile_detail_view(request: HttpRequest, username: Optional[str] = None) -> HttpResponse:
    """
    Displays detailed information for a specific user profile.

    Requires the user to be logged in. If no username is provided, the
    current user's profile is displayed.

    Args:
        request (HttpRequest): The HTTP request object.
        username (Optional[str]): The username of the profile to view. Defaults to None.

    Returns:
        HttpResponse: The rendered HTML response displaying the profile details.
    """
    user = request.user
    print(
        user.has_perm("subscriptions.basic"),
        user.has_perm("subscriptions.basic_ai"),
        user.has_perm("subscriptions.pro"),
        user.has_perm("subscriptions.advanced"),    
    )
    # user_groups = user.groups.all()
    # print("user_groups", user_groups)
    # if user_groups.filter(name__icontains='basic').exists():
    #     return HttpResponse("Congrats")
    profile_user_obj = get_object_or_404(User, username=username)
    is_me = profile_user_obj == user
    context = {
        "object": profile_user_obj,
        "instance": profile_user_obj,
        "owner": is_me,
    }
    return render(request, "profiles/detail.html", context)