# blog/urls.py
from django.urls import path, re_path
from .views import BlogPostListView, BlogPostDetailView

app_name = 'blogs'

urlpatterns = [
    path('', BlogPostListView.as_view(), name='post_list'),
    re_path(r'^(?P<slug>[\u0600-\u06FF\w-]+)/$', BlogPostDetailView.as_view(), name='post_detail'),
]