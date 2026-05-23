# Generated manually for DiscountUsage model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_discounts', '0001_initial'),
        ('orders', '0008_order_business_discount'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveBigIntegerField(verbose_name='مبلغ تخفیف (ریال)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ مصرف')),
                ('discount', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usages', to='business_discounts.businessdiscount', verbose_name='کد تخفیف')),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='discount_usage', to='orders.order', verbose_name='سفارش')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discount_usages', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'مصرف کد تخفیف',
                'verbose_name_plural': 'مصرف\u200cهای کد تخفیف',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='discountusage',
            constraint=models.UniqueConstraint(fields=('discount', 'user'), name='unique_discount_usage_per_user'),
        ),
    ]
