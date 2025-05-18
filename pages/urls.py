from django.urls import path
from . import views

app_name = 'pages'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.about_us_view, name='about_us'),
    path('contact/', views.contact_us_view, name='contact_us'),
]