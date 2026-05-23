from django.contrib import admin
from django.utils.html import format_html
from import_export.fields import Field

from accounts.helper import send_message
from config.import_export_utils import BaseExportResource, ExportOnlyModelAdmin
from config.jalali import format_jalali_datetime
import logging

from .models import Order, OrderItem, OrderStatusHistory, PaymentMethod

logger = logging.getLogger(__name__)


class PaymentMethodInline(admin.TabularInline):
    model = PaymentMethod
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['payment_type', 'amount', 'status', 'transaction_id', 'created_at', 'updated_at']


class OrderResource(BaseExportResource):
    order_number = Field(attribute='order_number', column_name='شماره سفارش')
    user_phone = Field(column_name='شماره موبایل')
    user_email = Field(column_name='ایمیل')
    status = Field(column_name='وضعیت سفارش')
    payment_status = Field(column_name='وضعیت پرداخت')
    total_amount = Field(attribute='total_amount', column_name='مبلغ کل')
    discount_amount = Field(attribute='discount_amount', column_name='مبلغ تخفیف')
    discount_code = Field(column_name='کد تخفیف')
    final_amount = Field(attribute='final_amount', column_name='مبلغ نهایی')
    unpaid_amount = Field(attribute='unpaid_amount', column_name='مبلغ پرداخت‌نشده')
    receiver_name = Field(attribute='receiver_name', column_name='نام گیرنده')
    receiver_phone = Field(attribute='receiver_phone', column_name='تلفن گیرنده')
    receiver_city = Field(attribute='receiver_city', column_name='شهر')
    receiver_postal_code = Field(attribute='receiver_postal_code', column_name='کد پستی')
    tracking_code = Field(attribute='tracking_code', column_name='کد رهگیری')
    created_at = Field(column_name='تاریخ ثبت')
    wallet_amount = Field(column_name='مبلغ کیف پول')
    wallet_status = Field(column_name='وضعیت کیف پول')
    gateway_amount = Field(column_name='مبلغ درگاه')
    gateway_status = Field(column_name='وضعیت درگاه')
    gateway_transaction = Field(column_name='شماره تراکنش درگاه')

    class Meta:
        model = Order
        fields = (
            'order_number', 'user_phone', 'user_email', 'status', 'payment_status',
            'total_amount', 'discount_amount', 'discount_code', 'final_amount', 'unpaid_amount',
            'receiver_name', 'receiver_phone', 'receiver_city', 'receiver_postal_code',
            'tracking_code', 'created_at',
            'wallet_amount', 'wallet_status', 'gateway_amount', 'gateway_status', 'gateway_transaction',
        )
        export_order = fields

    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 'business_discount',
        ).prefetch_related('payments')

    def dehydrate_user_phone(self, order):
        return order.user.phone_number

    def dehydrate_user_email(self, order):
        return order.user.email or ''

    def dehydrate_status(self, order):
        return order.get_status_display()

    def dehydrate_payment_status(self, order):
        return order.get_payment_status_display()

    def dehydrate_discount_code(self, order):
        if order.business_discount_id:
            return order.business_discount.code
        return ''

    def dehydrate_created_at(self, order):
        return format_jalali_datetime(order.created_at, fmt='%Y/%m/%d %H:%M')

    def _wallet_payment(self, order):
        for payment in order.payments.all():
            if payment.payment_type == 'wallet':
                return payment
        return None

    def _gateway_payment(self, order):
        for payment in order.payments.all():
            if payment.payment_type == 'gateway':
                return payment
        return None

    def dehydrate_wallet_amount(self, order):
        payment = self._wallet_payment(order)
        return payment.amount if payment else ''

    def dehydrate_wallet_status(self, order):
        payment = self._wallet_payment(order)
        return payment.get_status_display() if payment else ''

    def dehydrate_gateway_amount(self, order):
        payment = self._gateway_payment(order)
        return payment.amount if payment else ''

    def dehydrate_gateway_status(self, order):
        payment = self._gateway_payment(order)
        return payment.get_status_display() if payment else ''

    def dehydrate_gateway_transaction(self, order):
        payment = self._gateway_payment(order)
        return payment.transaction_id if payment and payment.transaction_id else ''


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_id_display', 'product_barcode', 'product_name', 'total_price']
    fields = [
        'product_id_display',
        'product_barcode',
        'product_name',
        'quantity',
        'unit_price',
        'total_price',
    ]

    def product_id_display(self, obj):
        return obj.product_id or '-'
    product_id_display.short_description = 'ID محصول'

    def product_barcode(self, obj):
        if obj.product_id:
            return obj.product.barcode
        return '-'
    product_barcode.short_description = 'بارکد محصول'

    def product_name(self, obj):
        if obj.product_id:
            return obj.product.name
        return '-'
    product_name.short_description = 'نام محصول'

    def has_add_permission(self, request, obj=None):
        return False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'changed_at', 'notes']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ExportOnlyModelAdmin):
    resource_class = OrderResource
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'discount_amount_display', 'final_amount_display', 'get_jalali_created_at',
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__phone_number', 'user__email']
    inlines = [OrderItemInline, OrderStatusHistoryInline, PaymentMethodInline]
    readonly_fields = ['order_number', 'get_jalali_created_at', 'get_jalali_updated_at', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': (
                'order_number', 'user', 'status', 'payment_status',
                'total_amount', 'discount_amount', 'business_discount',
                'final_amount', 'unpaid_amount', 'reward_applied',
            )
        }),
        ('اطلاعات گیرنده', {
            'fields': ('receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'receiver_postal_code')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('notes', 'tracking_code', 'get_jalali_created_at', 'get_jalali_updated_at')
        }),
    )

    def discount_amount_display(self, obj):
        if obj.discount_amount:
            code = obj.business_discount.code if obj.business_discount_id else '-'
            return format_html(
                '<span style="direction:ltr">{}</span> <small class="text-muted">({})</small>',
                f'{obj.discount_amount:,}',
                code,
            )
        return '-'
    discount_amount_display.short_description = 'تخفیف'

    def final_amount_display(self, obj):
        return format_html('<span style="direction:ltr">{}</span>', f"{obj.final_amount:,}")
    final_amount_display.short_description = 'مبلغ نهایی (ریال)'

    def get_jalali_created_at(self, obj):
        return obj.get_jalali_created_at()
    get_jalali_created_at.short_description = 'تاریخ ثبت'

    def get_jalali_updated_at(self, obj):
        return obj.get_jalali_updated_at()
    get_jalali_updated_at.short_description = 'تاریخ بروزرسانی'

    def save_model(self, request, obj, form, change):
        if change:
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                if old_obj.status != 'shipped' and obj.status == 'shipped':
                    send_message(
                        obj.user.phone_number,
                        '.',
                        template='order-send-confirmation',
                    )
                    logger.info('پیامک ارسال سفارش برای %s', obj.order_number)
            except Order.DoesNotExist:
                pass

        if change and 'status' in form.changed_data:
            OrderStatusHistory.objects.create(
                order=obj,
                old_status=form.initial['status'],
                new_status=obj.status,
                changed_by=request.user,
            )
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price_display', 'total_price_display']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['total_price']

    def unit_price_display(self, obj):
        return f'{obj.unit_price:,}'
    unit_price_display.short_description = 'قیمت واحد (ریال)'

    def total_price_display(self, obj):
        return f'{obj.total_price:,}'
    total_price_display.short_description = 'قیمت کل (ریال)'


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'old_status', 'new_status', 'changed_by', 'get_jalali_changed_at']
    list_filter = ['changed_at']
    search_fields = ['order__order_number']
    readonly_fields = ['changed_at', 'changed_by']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_type', 'amount', 'status', 'transaction_id', 'created_at']
    list_filter = ['payment_type', 'status', 'created_at']
    search_fields = ['order__order_number', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']
