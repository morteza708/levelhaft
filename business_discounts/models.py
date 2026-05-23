from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django_jalali.db import models as jmodels
import jdatetime


class BusinessDiscount(models.Model):
    sales_representative = models.CharField(
        max_length=30,
        verbose_name='نماینده فروش',
    )
    title = models.CharField(max_length=30, verbose_name='عنوان تخفیف')
    code = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        verbose_name='کد تخفیف',
    )
    usage_limit = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد مصرف باقی‌مانده',
    )
    percent = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='درصد تخفیف',
    )
    max_discount_amount = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        verbose_name='سقف مبلغ تخفیف (ریال)',
    )
    fixed_amount = models.PositiveBigIntegerField(
        blank=True,
        null=True,
        verbose_name='مبلغ ثابت تخفیف (ریال)',
    )
    start_date = jmodels.jDateField(verbose_name='تاریخ شروع')
    end_date = jmodels.jDateField(verbose_name='تاریخ پایان')
    allow_regular_users = models.BooleanField(
        default=False,
        verbose_name='کاربر عادی',
    )
    allow_beauticians = models.BooleanField(
        default=False,
        verbose_name='بیوتیشن',
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'کد تخفیف بیزنس'
        verbose_name_plural = 'کدهای تخفیف بیزنس'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.title}'

    def clean(self):
        has_percent = self.percent is not None
        has_fixed = self.fixed_amount is not None

        if has_percent and has_fixed:
            raise ValidationError('فقط یکی از درصد تخفیف یا مبلغ ثابت را وارد کنید.')

        if not has_percent and not has_fixed:
            raise ValidationError('یکی از درصد تخفیف یا مبلغ ثابت باید مشخص شود.')

        if has_percent:
            if self.percent < 1 or self.percent > 100:
                raise ValidationError('درصد تخفیف باید بین ۱ تا ۱۰۰ باشد.')
            if not self.max_discount_amount:
                raise ValidationError('برای تخفیف درصدی، سقف مبلغ تخفیف الزامی است.')
        elif self.max_discount_amount:
            raise ValidationError('در تخفیف مبلغ ثابت، سقف مبلغ تخفیف نباید پر شود.')

        if not self.allow_regular_users and not self.allow_beauticians:
            raise ValidationError('حداقل یکی از گزینه‌های کاربر عادی یا بیوتیشن باید انتخاب شود.')

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.')

    def save(self, *args, **kwargs):
        self.code = (self.code or '').strip().upper()
        self.full_clean()
        self._sync_auto_active_state()
        super().save(*args, **kwargs)

    def _sync_auto_active_state(self):
        today = jdatetime.date.today()
        if self.usage_limit <= 0:
            self.is_active = False
        elif self.end_date and self.end_date < today:
            self.is_active = False

    @property
    def discount_type_display(self):
        if self.percent:
            return f'{self.percent}% (حداکثر {self.max_discount_amount:,} ریال)'
        return f'{self.fixed_amount:,} ریال'


class DiscountUsage(models.Model):
    discount = models.ForeignKey(
        BusinessDiscount,
        on_delete=models.CASCADE,
        related_name='usages',
        verbose_name='کد تخفیف',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discount_usages',
        verbose_name='کاربر',
    )
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='discount_usage',
        verbose_name='سفارش',
    )
    amount = models.PositiveBigIntegerField(verbose_name='مبلغ تخفیف (ریال)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ مصرف')

    class Meta:
        verbose_name = 'مصرف کد تخفیف'
        verbose_name_plural = 'مصرف‌های کد تخفیف'
        constraints = [
            models.UniqueConstraint(
                fields=['discount', 'user'],
                name='unique_discount_usage_per_user',
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.discount.code} - {self.user.phone_number}'
