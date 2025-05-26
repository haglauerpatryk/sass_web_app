import pathlib
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings

from django.http import HttpResponse

from visits.models import PageVisit
from toolbox.decorators import light_toolbox
from toolbox.basic import ToolBox
from toolbox.utils import reroute_with_retry
LOGIN_URL = settings.LOGIN_URL

this_dir = pathlib.Path(__file__).resolve().parent

@ToolBox().catch_error({
    ValueError: lambda e, ctx: reroute_with_retry(
        home_2view,
        toolbox=ctx["toolbox"],
        retries=2,
        delay=0.1
    )(e, ctx)
})
def home_view(request, *args, **kwargs):
    raise ValueError("Oops")


number = None

def home_2view(request, *args, **kwargs):
    global number
    if not number:
        number = 1
        raise ValueError("Oops!")
    number = None
    if request.user.is_authenticated:
        print(request.user.first_name)
    return about_view(request, *args, **kwargs)


@light_toolbox
def about_view(request, *args, **kwargs):
    qs = PageVisit.objects.all()
    page_qs = PageVisit.objects.filter(path=request.path)
    try:
        percent = (page_qs.count() * 100.0) / qs.count()
    except:
        percent = 0
    my_title = "My Page"
    html_template = "home.html"
    my_context = {
        "page_title": my_title,
        "page_visit_count": page_qs.count(),
        "percent": percent,
        "total_visit_count": qs.count(),
    }
    PageVisit.objects.create(path=request.path)
    return render(request, html_template, my_context)


def my_old_home_page_view(request, *args, **kwargs):
    my_title = "My Page"
    my_context = {
        "page_title": my_title
    }
    html_ = """
    <!DOCTYPE html>
<html>

<body>
    <h1>{page_title} anything?</h1>
</body>
</html>    
""".format(**my_context) # page_title=my_title
    # html_file_path = this_dir / "home.html"
    # html_ = html_file_path.read_text()
    return HttpResponse(html_)

VALID_CODE = "abc123"


@light_toolbox
def pw_protected_view(request, *args, **kwargs):
    is_allowed = request.session.get('protected_page_allowed') or 0
    # print(request.session.get('protected_page_allowed'), type(request.session.get('protected_page_allowed')))
    if request.method == "POST":
        user_pw_sent = request.POST.get("code") or None
        if user_pw_sent == VALID_CODE:
            is_allowed = 1
            request.session['protected_page_allowed'] = is_allowed
    if is_allowed:
        return render(request, "protected/view.html", {})
    return render(request, "protected/entry.html", {})


@light_toolbox
@login_required
def user_only_view(request, *args, **kwargs):
    # print(request.user.is_staff)
    return render(request, "protected/user-only.html", {})


@light_toolbox
@staff_member_required(login_url=LOGIN_URL)
def staff_only_view(request, *args, **kwargs):
    return render(request, "protected/user-only.html", {})