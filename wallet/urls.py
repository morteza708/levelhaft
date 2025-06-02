from django.urls import path
from . import views

app_name = 'wallet'
 
urlpatterns = [
    path('', views.wallet_detail, name='detail'),
    path('charge/', views.charge_wallet, name='charge'),
    path('charge/callback/', views.charge_callback, name='charge_callback'),
] 