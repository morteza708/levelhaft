"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import render
from products.views import upload_file

admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.index_title = settings.ADMIN_INDEX_TITLE 

# Test views for error pages
def test_500(request):
    return render(request, '500.html')

def test_403(request):
    return render(request, '403.html')

def test_400(request):
    return render(request, '400.html')

def test_error_pages(request):
    return render(request, 'error_test.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor5/upload/', upload_file, name='custom_upload_file'),
    path('', include('pages.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('products/', include('products.urls', namespace='products')),
    path('blogs/', include('blogs.urls', namespace='blogs')),
    path('workshop/', include('workshop.urls', namespace='workshop')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('wallet/', include('wallet.urls', namespace='wallet')),
    
    # SEO URLs
    path('sitemap.xml', include('pages.urls')),
    path('robots.txt', lambda request: HttpResponse(open('robots.txt').read(), content_type='text/plain')),
    
    # Test URLs for error pages (only in development)
    path('test-errors/', test_error_pages, name='test_errors'),
    path('test-500/', test_500, name='test_500'),
    path('test-403/', test_403, name='test_403'),
    path('test-400/', test_400, name='test_400'),
]
urlpatterns += [
    path("ckeditor5/", include('django_ckeditor_5.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


