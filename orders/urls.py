from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('list/', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),
    path('<int:order_id>/start-payment/', views.order_start_payment, name='order_start_payment'),
    path('payment/callback/', views.order_payment_callback, name='order_payment_callback'),
] 