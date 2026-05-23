# Generated manually for business_discounts app

import django_jalali.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessDiscount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sales_representative', models.CharField(max_length=30, unique=True, verbose_name='نماینده فروش')),
                ('title', models.CharField(max_length=30, verbose_name='عنوان تخفیف')),
                ('code', models.CharField(db_index=True, max_length=30, unique=True, verbose_name='کد تخفیف')),
                ('usage_limit', models.PositiveIntegerField(default=0, verbose_name='تعداد مصرف باقی\u200cمانده')),
                ('percent', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='درصد تخفیف')),
                ('max_discount_amount', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='سقف مبلغ تخفیف (ریال)')),
                ('fixed_amount', models.PositiveBigIntegerField(blank=True, null=True, verbose_name='مبلغ ثابت تخفیف (ریال)')),
                ('start_date', django_jalali.db.models.jDateField(verbose_name='تاریخ شروع')),
                ('end_date', django_jalali.db.models.jDateField(verbose_name='تاریخ پایان')),
                ('allow_regular_users', models.BooleanField(default=False, verbose_name='کاربر عادی')),
                ('allow_beauticians', models.BooleanField(default=False, verbose_name='بیوتیشن')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
            ],
            options={
                'verbose_name': 'کد تخفیف بیزنس',
                'verbose_name_plural': 'کدهای تخفیف بیزنس',
                'ordering': ['-created_at'],
            },
        ),
    ]
