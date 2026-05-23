# Generated manually to allow multiple campaigns per sales representative

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business_discounts', '0002_discountusage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='businessdiscount',
            name='sales_representative',
            field=models.CharField(max_length=30, verbose_name='نماینده فروش'),
        ),
    ]
