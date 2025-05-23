from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django_jalali.db import models as jmodels
from django.conf import settings
import random
import jdatetime



class WorkshopBrand(models.Model):
    name = models.CharField(max_length=255, verbose_name="نام برند")
    image = models.ImageField(upload_to='workshop-brands/', verbose_name="لوگو برند")

    class Meta:
        verbose_name = "برند ورکشاپ"
        verbose_name_plural = "برندهای ورکشاپ"

    def __str__(self):
        return self.name


class Workshop(models.Model):
    brand = models.ForeignKey(WorkshopBrand, on_delete=models.CASCADE, related_name="workshops", verbose_name="برند ورکشاپ")
    title = models.CharField(max_length=255, verbose_name="عنوان ورکشاپ")
    date = jmodels.jDateField(verbose_name="تاریخ برگزاری")
    city = models.CharField(max_length=100, verbose_name="شهر محل برگزاری")
    price = models.PositiveIntegerField(verbose_name="قیمت ورکشاپ (ریال)")
    capacity = models.PositiveIntegerField(verbose_name="ظرفیت ورکشاپ", default=30)
    description = CKEditor5Field(verbose_name="توضیحات")
    image = models.ImageField(upload_to='workshops/', verbose_name="تصویر ورکشاپ")

    class Meta:
        verbose_name = "ورکشاپ"
        verbose_name_plural = "ورکشاپ‌ها"

    def __str__(self):
        return f"{self.title} - {self.brand.name}"
    
    

class WorkshopRegistration(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    )

    workshop = models.ForeignKey(Workshop, on_delete=models.CASCADE, related_name="registrations", verbose_name="ورکشاپ")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="workshop_registrations", verbose_name="کاربر")
    first_name_en = models.CharField(max_length=255, verbose_name="نام به انگلیسی")
    last_name_en = models.CharField(max_length=255, verbose_name="نام خانوادگی به انگلیسی")
    clinic_name = models.CharField(max_length=255, verbose_name="نام کلینیک")
    city = models.CharField(max_length=100, verbose_name="شهر محل فعالیت")
    address = models.TextField(verbose_name="آدرس محل فعالیت")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت ثبت نام")
    barcode = models.CharField(max_length=20, blank=True, unique=True, verbose_name="بارکد شرکت کننده")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "ثبت نام ورکشاپ"
        verbose_name_plural = "ثبت نام‌های ورکشاپ"

    def get_jalali_created_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_created_at.short_description = 'تاریخ ثبت نام'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.workshop.title}"

    def save(self, *args, **kwargs):
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)

    def generate_barcode(self):
        prefix = "WR"
        brand_letter = self.get_brand_letter()
        random_digits = str(random.randint(10000, 99999)).zfill(5)
        return f"{prefix}{brand_letter}{random_digits}"

    def get_brand_letter(self):
        mapping = {
            "دکتر بلتر": "B",
            "دکتر ریمپلر": "R",
            "ایزابل لنکری": "I",
            "راکوتن": "RA",
            "DS V-LINE": "D",
            "کیسی": "C",
        }
        return mapping.get(self.workshop.brand.name, "X")

class WorkshopRegistrationHistory(models.Model):
    """
    مدل برای ذخیره تاریخچه تغییرات وضعیت ثبت‌نام
    """
    registration = models.ForeignKey(WorkshopRegistration, on_delete=models.CASCADE, related_name='history', verbose_name="ثبت‌نام")
    old_status = models.CharField(max_length=10, verbose_name="وضعیت قبلی")
    new_status = models.CharField(max_length=10, verbose_name="وضعیت جدید")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تغییر")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="تغییر دهنده")

    class Meta:
        verbose_name = "تاریخچه وضعیت ثبت‌نام"
        verbose_name_plural = "تاریخچه وضعیت‌های ثبت‌نام"
        ordering = ['-changed_at']

    def __str__(self):
        return f"تغییر وضعیت ثبت‌نام {self.registration.user.get_full_name()} از {self.old_status} به {self.new_status}"

    def get_jalali_changed_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.changed_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_changed_at.short_description = 'تاریخ تغییر'