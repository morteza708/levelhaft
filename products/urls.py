from django.urls import path, re_path
from . import views

app_name = 'products'

urlpatterns = [
    re_path(r'^line/(?P<slug>[\w\u0600-\u06FF-]+)/$', views.line_products, name='line_products'),
    re_path(r'^product/(?P<slug>[\w\u0600-\u06FF-]+)/$', views.product_detail, name='product_detail'),
    re_path(r'^product/(?P<slug>[\w\u0600-\u06FF-]+)/comment/$', views.submit_comment, name='submit_comment'),
    path('admin/comment/<int:comment_id>/approve/', views.approve_comment, name='admin_approve_comment'),
    path('admin/comment/<int:comment_id>/reject/', views.reject_comment, name='admin_reject_comment'),
    path('search/', views.search_page, name='search_page'),
    path('search/results/', views.product_search, name='product_search'),
    path('consult/', views.consult_view, name='consult'),
    path('consult/results/', views.consult_search, name='consult_search'),
    path('accessories/', views.accessories_list_view, name='accessories_list'),
]
