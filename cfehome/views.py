import pathlib
from django.shortcuts import render
from django.http import HttpResponse

from visits.models import PageVisit

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    return about_view(request, *args, **kwargs)


def about_view(request, *args, **kwargs):
    qs = PageVisit.objects.all()
    page_qs = PageVisit.objects.filter(path=request.path)
    try: 
        percent = page_qs.count() / qs.count() * 100.0
    except:
        percent = 0
    my_title = "My Page"
    my_context = {
        "page_title": my_title,
        "page_visit_count": page_qs.count(),
        "percentage": percent,
        "total_visit_count": qs.count(),
    }
    path = request.path
    print(path)
    html_template = "home.html"
    PageVisit.objects.create(path=request.path)

    return render(request, html_template, my_context)


def my_old_home_page_view(request, *args, **kwargs):
    my_title = "My Page"
    my_context = {"page_title": my_title}
    html_ = """
<!DOCTYPE html>
<html>
    <head>

    </head>
    <body>
        <h1>Home</h1>
        <p>Welcome to {page_title}.</p>
    </body>
</html>
""".format(**my_context)
    html_file_path = this_dir / "templates" / "home.html"
    html_ = html_file_path.read_text()
    return HttpResponse(html_)