from django.contrib.auth.models import AbstractUser
from django.db import models
from django_jalali.db import models as jalali_models
from .managers import CustomUserManager


class CustomUser(AbstractUser):
    """
    A CustomUser model for managing users with phone number and OTP authentication
    """
    DoesNotExist = None
    username = None
    phone_number = models.CharField(max_length=11, unique=True, db_index=True, verbose_name="شماره موبایل")
    otp_code = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="کد تایید")
    otp_code_created = models.DateTimeField(auto_now=True, verbose_name="زمان ایجاد کد تایید")
    is_beautician = models.BooleanField(default=False, verbose_name="بیوتیشن")  # Field to check if user is beautician
    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="نام")
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="نام خانوادگی")
    email = models.EmailField(max_length=50, blank=True, null=True, verbose_name="ایمیل")

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    backend = 'accounts.backends.PhoneAuthenticationBackend'

    def __str__(self):
        return self.phone_number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # همگام‌سازی is_beautician با CustomerProfile
        if hasattr(self, 'profile'):
            self.profile.is_beautician = self.is_beautician
            self.profile.save(update_fields=['is_beautician'])

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربرها"


class CustomerProfile(models.Model):
    objects = models.Manager()
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=30, blank=True, null=True, verbose_name="نام")
    last_name = models.CharField(max_length=30, blank=True, null=True, verbose_name="نام خانوادگی")
    birth_date = jalali_models.jDateField(blank=True, null=True, verbose_name="تاریخ تولد")
    age = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="سن")
    gender = models.CharField(max_length=10, choices=[('male', 'مرد'), ('female', 'زن')], blank=True, null=True,
                              verbose_name="جنسیت")
    email = models.EmailField(blank=True, null=True)
    clinic_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام کلینیک")
    activity_city = models.CharField(max_length=50, blank=True, null=True, verbose_name="شهر محل فعالیت")
    activity_history = models.CharField(max_length=100, blank=True, null=True, verbose_name="سابقه فعالیت")
    brand_used = models.CharField(max_length=255, blank=True, null=True,
                                  verbose_name="چه برند هایی تاکنون استفاده کرده اید؟")
    instagram_url = models.CharField(max_length=255, blank=True, null=True, verbose_name="لینک پیج اینستاگرام")
    is_beautician = models.BooleanField(default=False, verbose_name="بیوتیشن")

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''} ({self.user.phone_number})"

    class Meta:
        verbose_name = "پروفایل مشتری"
        verbose_name_plural = "پروفایل‌های مشتری"


class Address(models.Model):
    objects = models.Manager()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone_number} - {self.city}"

    class Meta:
        verbose_name = "آدرس"
        verbose_name_plural = "آدرس‌ها"











