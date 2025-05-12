from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from .utils import create_persian_slug

class BlogCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام دسته بندی")
    slug = models.SlugField(max_length=255, allow_unicode=True, unique=True, verbose_name="اسلاگ دسته بندی")

    class Meta:
        verbose_name = "دسته بندی مقاله"
        verbose_name_plural = "دسته بندی های مقالات"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_persian_slug(self.name)
        super().save(*args, **kwargs)

class BlogPost(models.Model):
    STATUS_CHOICES = (
        ('draft', 'پیش نویس'),
        ('published', 'منتشر شده'),
    )

    title = models.CharField(max_length=255, verbose_name="عنوان مقاله")
    slug = models.SlugField(max_length=255, allow_unicode=True, unique=True, verbose_name="اسلاگ مقاله")
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts", verbose_name="دسته بندی")
    summary = models.TextField(max_length=300, verbose_name="خلاصه متا توضیحات سئو")
    content = CKEditor5Field(verbose_name="محتوای مقاله")
    image = models.ImageField(upload_to='blog-images/', null=True, blank=True, verbose_name="تصویر کاور")
    tags = models.CharField(max_length=255, blank=True, null=True, verbose_name="تگ ها (با کاما جدا کنید)")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="وضعیت انتشار")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_persian_slug(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blogs:post_detail', kwargs={'slug': self.slug})

