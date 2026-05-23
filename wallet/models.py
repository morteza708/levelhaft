from django.db import models
from django.conf import settings
from config.jalali import format_jalali_datetime

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'کیف پول'
        verbose_name_plural = 'کیف پول ها'

    def __str__(self):
        username = getattr(self.user, 'username', 'نامشخص')
        return f"کیف پول {username} - موجودی: {self.balance} ریال"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'افزایش موجودی'),
        ('withdraw', 'برداشت برای سفارش'),
        ('reward', 'پاداش خرید'),
        ('refund', 'بازگشت سفارش لغو شده'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.PositiveIntegerField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pasargad_url_id = models.CharField(max_length=200, blank=True, null=True, verbose_name="شناسه تراکنش پاسارگاد")


    class Meta:
        verbose_name = 'تراکنش کیف پول'
        verbose_name_plural = 'تراکنش های کیف پول'

    def __str__(self):
        return f"{self.wallet.user.username} - {self.get_type_display()} - {self.amount} ریال"

    def get_jalali_created_at(self):
        return format_jalali_datetime(self.created_at, fmt='%Y/%m/%d %H:%M')
    get_jalali_created_at.short_description = 'تاریخ (شمسی)'

