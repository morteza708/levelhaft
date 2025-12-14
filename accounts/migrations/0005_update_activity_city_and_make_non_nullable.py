# Generated manually for faster migration

from django.db import migrations, models


def update_null_fields(apps, schema_editor):
    """به‌روزرسانی تمام فیلدهای اجباری که NULL هستند"""
    CustomerProfile = apps.get_model('accounts', 'CustomerProfile')
    
    # به‌روزرسانی دسته‌ای برای سرعت بیشتر - همه فیلدها در یک query
    CustomerProfile.objects.filter(
        clinic_name__isnull=True
    ).update(clinic_name='نامشخص')
    
    CustomerProfile.objects.filter(
        activity_city__isnull=True
    ).update(activity_city='نامشخص')
    
    CustomerProfile.objects.filter(
        activity_history__isnull=True
    ).update(activity_history='نامشخص')
    
    CustomerProfile.objects.filter(
        brand_used__isnull=True
    ).update(brand_used='نامشخص')
    
    CustomerProfile.objects.filter(
        instagram_url__isnull=True
    ).update(instagram_url='نامشخص')


def reverse_update(apps, schema_editor):
    """برای rollback - نیازی نیست"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_alter_customuser_email_alter_customuser_first_name_and_more'),
    ]

    operations = [
        # ابتدا تمام رکوردهای NULL را به‌روزرسانی می‌کنیم
        migrations.RunPython(update_null_fields, reverse_update),
        # سپس تمام فیلدهای اجباری را non-nullable می‌کنیم
        migrations.AlterField(
            model_name='customerprofile',
            name='clinic_name',
            field=models.CharField(max_length=100, verbose_name='نام کلینیک'),
        ),
        migrations.AlterField(
            model_name='customerprofile',
            name='activity_city',
            field=models.CharField(max_length=50, verbose_name='شهر محل فعالیت'),
        ),
        migrations.AlterField(
            model_name='customerprofile',
            name='activity_history',
            field=models.CharField(max_length=100, verbose_name='سابقه فعالیت'),
        ),
        migrations.AlterField(
            model_name='customerprofile',
            name='brand_used',
            field=models.CharField(max_length=255, verbose_name='چه برند هایی تاکنون استفاده کرده اید؟'),
        ),
        migrations.AlterField(
            model_name='customerprofile',
            name='instagram_url',
            field=models.CharField(max_length=255, verbose_name='لینک پیج اینستاگرام'),
        ),
    ]

