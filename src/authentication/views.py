from typing import Optional
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse

from toolbox.basic import ToolBox
from toolbox.decorators import light_toolbox


# REDUNDANT CODE

User = get_user_model()


@light_toolbox
def login_view(request: HttpRequest) -> HttpResponse:
    """
    Handle user login by validating credentials and starting a session.

    Args:
        request (HttpRequest): The HTTP request object containing user input.

    Returns:
        HttpResponse: 
            - Renders the login page if the method is GET or credentials are invalid.
            - Redirects to the homepage if login is successful.
    """
    if request.method == "POST":
        username: Optional[str] = request.POST.get("username") or None
        password: Optional[str] = request.POST.get("password") or None
        if all([username, password]):
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
    return render(request, "authentication/login.html", {})


@light_toolbox
def register_view(request: HttpRequest) -> HttpResponse:
    """
    Handle user registration by creating a new account with the provided data.

    Args:
        request (HttpRequest): The HTTP request object containing user input.

    Returns:
        HttpResponse:
            - Renders the registration page if the method is GET or registration fails.
            - Redirects to the login page after successful registration.
    """
    if request.method == "POST":
        username = request.POST.get("username") or None
        email = request.POST.get("email") or None
        password = request.POST.get("password") or None
        # Django Forms
        # username_exists = User.objects.filter(username__iexact=username).exists()
        # email_exists = User.objects.filter(email__iexact=email).exists()
        try:
            User.objects.create_user(username, email=email, password=password)
        except:
            pass
    return render(request, "authentication/register.html", {})