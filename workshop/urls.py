from django.urls import path
from . import views

app_name = 'workshop'

urlpatterns = [
    path('', views.WorkshopListView.as_view(), name='workshop_list'),
    path('brand/<int:brand_id>/', views.WorkshopBrandView.as_view(), name='workshop_brand'),
    path('<int:pk>/', views.WorkshopDetailView.as_view(), name='workshop_detail'),
    path('<int:workshop_id>/register/', views.WorkshopRegistrationView.as_view(), name='register'),
    path('approved-registrations/', views.ApprovedRegistrationsView.as_view(), name='approved_registrations'),
]
