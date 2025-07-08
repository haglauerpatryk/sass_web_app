from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

def home_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return about_view(request, *args, **kwargs)


def about_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    my_title = "My Page"
    html_template = "home.html"
    my_context = {
        "page_title": my_title,
    }
    return render(request, html_template, my_context)


@login_required
def user_only_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "protected/user-only.html", {})


@staff_member_required
def staff_only_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    return render(request, "protected/user-only.html", {})