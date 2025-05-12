# blog/admin.py
from django.contrib import admin
from .models import BlogPost, BlogCategory

@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ('name',)

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'summary', 'tags')
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

