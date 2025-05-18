from django.db import models
from jalali_date import datetime2jalali

# Create your models here.

class ContactMessage(models.Model):
    name = models.CharField("نام", max_length=100)
    email = models.EmailField("ایمیل")
    subject = models.CharField("موضوع", max_length=200)
    message = models.TextField("متن پیام")
    created_at = models.DateTimeField("تاریخ ارسال", auto_now_add=True)
    is_read = models.BooleanField("خوانده شده", default=False)

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"

    @property
    def created_at_jalali(self):
        return datetime2jalali(self.created_at).strftime('%Y/%m/%d - %H:%M')
