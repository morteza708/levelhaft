# blog/views.py
from django.views.generic import ListView, DetailView
from .models import BlogPost, BlogCategory

class BlogPostListView(ListView):
    model = BlogPost
    template_name = 'blogs/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 6

    def get_queryset(self):
        return BlogPost.objects.filter(status='published').select_related('category')

class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blogs/blog_detail.html'
    context_object_name = 'post'