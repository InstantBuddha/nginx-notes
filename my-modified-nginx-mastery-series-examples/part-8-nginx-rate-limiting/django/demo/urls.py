from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.http import HttpResponse

#urlpatterns = [
#    path('admin/', admin.site.urls),
#    path('test/', TemplateView.as_view(template_name="index.html")),
#]

# My custom modifications:
def home_view(request):
    return HttpResponse("Home Page")

def test_view(request):
    return HttpResponse("Test Page")

def ip_view(request):
    # Get the real IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # In case of multiple IPs, take the first one
    else:
        ip = request.META.get('REMOTE_ADDR')  # Default to REMOTE_ADDR

    return HttpResponse(f"Your IP is: {ip}")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),  # Root URL '/'
    path('test/', test_view, name='test'),  # URL '/test/'
    path('ip/', ip_view, name='ip'),  # URL '/ip/'
]