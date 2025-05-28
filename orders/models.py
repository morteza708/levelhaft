from django.db import models
from django.conf import settings
from django_jalali.db import models as jmodels
import jdatetime
from products.models import Product
from django.db.models.signals import post_save
from django.dispatch import receiver
from wallet.services.wallet_services import apply_order_reward

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار تایید'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('failed', 'پرداخت ناموفق'),
        ('refunded', 'مسترد شده'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders', verbose_name="کاربر")
    order_number = models.CharField(max_length=20, unique=True, verbose_name="شماره سفارش")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت سفارش")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="وضعیت پرداخت")
    total_amount = models.PositiveBigIntegerField(verbose_name="مبلغ کل (ریال)")
    discount_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ تخفیف (ریال)")
    final_amount = models.PositiveBigIntegerField(verbose_name="مبلغ نهایی (ریال)")
    unpaid_amount = models.PositiveBigIntegerField(default=0, verbose_name="مبلغ پرداخت نشده (ریال)")
    reward_applied = models.BooleanField(default=False, verbose_name="پاداش اعمال شده")
    
    # اطلاعات گیرنده
    receiver_name = models.CharField(max_length=255, verbose_name="نام گیرنده")
    receiver_phone = models.CharField(max_length=15, verbose_name="شماره تماس گیرنده")
    receiver_address = models.TextField(verbose_name="آدرس گیرنده")
    receiver_city = models.CharField(max_length=100, verbose_name="شهر گیرنده")
    receiver_postal_code = models.CharField(max_length=10, verbose_name="کد پستی")
    
    # اطلاعات تکمیلی
    notes = models.TextField(blank=True, verbose_name="توضیحات سفارش")
    tracking_code = models.CharField(max_length=50, blank=True, verbose_name="کد رهگیری تیپاکس")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"سفارش {self.order_number} - {self.user.get_full_name()}"

    def get_jalali_created_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_created_at.short_description = 'تاریخ ثبت'

    def get_jalali_updated_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_updated_at.short_description = 'تاریخ بروزرسانی'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and self.status == 'completed':
            # اعمال پاداش خرید
            apply_order_reward(self.user, self.get_reward_amount(), self.order_number)

    def generate_order_number(self):
        import random
        import string
        prefix = "ORD"
        date_part = jdatetime.datetime.now().strftime('%y%m%d')
        while True:
            random_part = ''.join(random.choices(string.digits, k=4))  # تولید ۴ رقم تصادفی
            code = f"{prefix}{date_part}{random_part}"
            if not Order.objects.filter(order_number=code).exists():
                return code

    @property
    def can_be_cancelled(self):
        return self.status == 'pending'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="سفارش")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items', verbose_name="محصول")
    quantity = models.PositiveIntegerField(verbose_name="تعداد")
    unit_price = models.PositiveIntegerField(verbose_name="قیمت واحد (ریال)")
    total_price = models.PositiveBigIntegerField(verbose_name="قیمت کل (ریال)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "آیتم سفارش"
        verbose_name_plural = "آیتم‌های سفارش"

    def __str__(self):
        return f"{self.product.name} - {self.quantity} عدد"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history', verbose_name="سفارش")
    old_status = models.CharField(max_length=20, verbose_name="وضعیت قبلی")
    new_status = models.CharField(max_length=20, verbose_name="وضعیت جدید")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ تغییر")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="تغییر دهنده")
    notes = models.TextField(blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "تاریخچه وضعیت سفارش"
        verbose_name_plural = "تاریخچه وضعیت‌های سفارش"
        ordering = ['-changed_at']

    def __str__(self):
        return f"تغییر وضعیت سفارش {self.order.order_number} از {self.old_status} به {self.new_status}"

    def get_jalali_changed_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.changed_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_changed_at.short_description = 'تاریخ تغییر' 

@receiver(post_save, sender=Order)
def handle_order_status_change(sender, instance, created, **kwargs):
    if not created and instance.payment_status == 'paid' and not instance.reward_applied:
        print(f"[سیگنال سفارش] پاداش برای سفارش {instance.order_number} در حال اعمال است...")
        apply_order_reward(instance)
        instance.reward_applied = True
        instance.save(update_fields=["reward_applied"]) 

class PaymentMethod(models.Model):
    PAYMENT_TYPES = (
        ('wallet', 'کیف پول'),
        ('gateway', 'درگاه پرداخت'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار پرداخت'),
        ('completed', 'پرداخت شده'),
        ('failed', 'ناموفق'),
    )

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, verbose_name="نوع پرداخت")
    amount = models.PositiveBigIntegerField(verbose_name="مبلغ پرداختی")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت پرداخت")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="شماره تراکنش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "روش پرداخت"
        verbose_name_plural = "روش‌های پرداخت"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount:,} ریال"

    def get_jalali_created_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.created_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_created_at.short_description = 'تاریخ ایجاد'

    def get_jalali_updated_at(self):
        return jdatetime.datetime.fromgregorian(datetime=self.updated_at).strftime('%Y/%m/%d %H:%M:%S')
    get_jalali_updated_at.short_description = 'تاریخ بروزرسانی' 