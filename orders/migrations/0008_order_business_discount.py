# Generated manually for business discount FK on Order

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_order_pasargad_url_id'),
        ('business_discounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='business_discount',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='business_discounts.businessdiscount',
                verbose_name='کد تخفیف بیزنس',
            ),
        ),
    ]
