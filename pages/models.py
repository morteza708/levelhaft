from django.db import models
from jalali_date import datetime2jalali

# Create your models here.

class SliderSlide(models.Model):
    LINK_TYPE_CHOICES = [
        ('url', 'URL کامل'),
        ('named_url', 'نام URL Pattern'),
    ]
    
    title = models.CharField("عنوان (برای شناسایی در ادمین)", max_length=200, blank=True, null=True, help_text="این فیلد فقط برای شناسایی اسلاید در پنل ادمین است")
    image = models.ImageField("تصویر اصلی (دسکتاپ)", upload_to='slider/', help_text="تصویر با کیفیت بالا برای نمایش در دسکتاپ")
    image_mobile = models.ImageField("تصویر موبایل (اختیاری)", upload_to='slider/mobile/', blank=True, null=True, help_text="اگر خالی باشد، از تصویر اصلی استفاده می‌شود")
    link_type = models.CharField("نوع لینک", max_length=20, choices=LINK_TYPE_CHOICES, default='url')
    link_url = models.CharField("آدرس لینک", max_length=500, blank=True, help_text="بسته به نوع لینک: URL کامل (مثل https://levelhaft.com/workshop/14/) یا نام URL pattern (مثل products:consult)")
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0, help_text="عدد کمتر = نمایش زودتر")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "اسلاید"
        verbose_name_plural = "اسلایدها"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f"اسلاید {self.id}"

    def get_link(self):
        """برگرداندن لینک مناسب"""
        if not self.link_url:
            return '#'
        return self.link_url
    
    def get_link_for_template(self):
        """برگرداندن لینک برای استفاده در template"""
        if not self.link_url:
            return '#'
        if self.link_type == 'named_url':
            # در template باید از {% url %} استفاده شود
            return self.link_url
        return self.link_url

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
