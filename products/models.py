from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django_ckeditor_5.fields import CKEditor5Field
from .utils import convert_to_english_digits, create_persian_slug
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

# --- دسته‌بندی‌های قابل توسعه ---

class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام برند")
    image = models.ImageField(upload_to='brand-logos/', blank=True, null=True, verbose_name="لوگو برند")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات برند")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "برند"
        verbose_name_plural = "برندها"

    def __str__(self):
        return self.name

class Line(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='lines')
    name = models.CharField(max_length=100, verbose_name="لاین محصول")
    slug = models.SlugField(blank=True, allow_unicode=True, verbose_name="اسلاگ لاین")

    def __str__(self):
        return f"{self.brand.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_persian_slug(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "لاین"
        verbose_name_plural = "لاین‌ها"

class UsageType(models.Model):
    name = models.CharField(max_length=50, verbose_name="نوع مصرف")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نوع مصرف"
        verbose_name_plural = "انواع مصرف"

class ProductModel(models.Model):
    name = models.CharField(max_length=50, verbose_name="مدل محصول")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "مدل محصول"
        verbose_name_plural = "مدل‌های محصول"

class SkinType(models.Model):
    name = models.CharField(max_length=50, verbose_name="نوع پوست")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نوع پوست"
        verbose_name_plural = "نوع پوست‌ها"

class SkinCondition(models.Model):
    name = models.CharField(max_length=50, verbose_name="ویژگی درمانی محصول")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "ویژگی درمانی محصول"
        verbose_name_plural = "ویژگی‌های درمانی محصول"

class VolumeUnit(models.Model):
    name = models.CharField(max_length=20, verbose_name="واحد حجم محصول")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "واحد حجم"
        verbose_name_plural = "واحدهای حجم"

# --- محصول ---

class ProductManager(models.Manager):
    def for_user(self, user):
        if user.is_authenticated:
            if hasattr(user, "profile") and user.profile.is_beautician:
                return self.get_queryset().annotate(price=models.F('price_level_1'))
            else:
                return self.get_queryset().annotate(price=models.F('price_level_2'))
        return self.get_queryset().filter(price_level_2__isnull=True)

class Product(models.Model):
    barcode = models.CharField(max_length=6, unique=True, verbose_name="کد محصول")
    name = models.CharField(max_length=255, verbose_name="نام محصول")
    slug = models.SlugField(blank=True, allow_unicode=True, verbose_name="اسلاگ محصول")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="برند")
    line = models.ForeignKey(Line, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="لاین محصول")
    usage_type = models.ForeignKey(UsageType, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="نوع مصرف")
    model = models.ForeignKey(ProductModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="مدل محصول")
    skin_types = models.ManyToManyField(SkinType, blank=True, related_name="products", verbose_name="ویژگی محصول")
    skin_conditions = models.ManyToManyField(SkinCondition, blank=True, related_name="products", verbose_name="ویژگی درمانی محصول")
    volume_value = models.PositiveIntegerField(null=True, blank=True, verbose_name="مقدار حجم")
    volume_unit = models.ForeignKey(VolumeUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name="products", verbose_name="واحد حجم")
    short_description = models.TextField(blank=True, null=True, verbose_name="توضیحات کوتاه")
    long_description = CKEditor5Field(blank=True, null=True, verbose_name="توضیحات بلند")
    price_level_1 = models.PositiveIntegerField(blank=True, null=True, verbose_name="قیمت برای کاربران بیوتیشن")
    price_level_2 = models.PositiveIntegerField(blank=True, null=True, verbose_name="قیمت برای کاربران عادی")
    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی")
    is_featured = models.BooleanField(default=False, verbose_name="محصول ویژه")
    show_on_home = models.BooleanField(default=False, verbose_name="نمایش در صفحه اصلی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    objects = ProductManager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        # تبدیل اعداد فارسی به انگلیسی
        if self.volume_value:
            self.volume_value = convert_to_english_digits(str(self.volume_value))
        if self.price_level_1:
            self.price_level_1 = convert_to_english_digits(str(self.price_level_1))
        if self.price_level_2:
            self.price_level_2 = convert_to_english_digits(str(self.price_level_2))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = create_persian_slug(self.name)
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="محصول")
    image = models.ImageField(upload_to='product-images/', verbose_name="تصویر محصول")

    def __str__(self):
        return f"{self.product.name} - {self.image.name}"

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"

class Comment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار تایید'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده')
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(verbose_name='متن نظر')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

    def get_status_color(self):
        status_colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        return status_colors.get(self.status, 'secondary')