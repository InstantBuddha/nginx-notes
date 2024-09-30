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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),  # Root URL '/'
    path('test/', test_view, name='test'),  # URL '/test/'
]