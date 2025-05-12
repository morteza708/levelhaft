from django.urls import path
from django.contrib.auth.views import LogoutView

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('verify/', views.verify_otp_view, name='verify'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('beautican_form/', views.beautician_request, name='beautician_form'),
    path('beautician-request/', views.beautician_request, name='beautician_request'),
    path('my_account/', views.my_account_view, name='my_account'),
    path('update-profile/', views.update_profile_view, name='update_profile'),
    path('add-address/', views.add_address_view, name='add_address'),
    path('logout/', LogoutView.as_view(next_page='pages:home'), name='logout'),
]