from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory, PaymentMethod
from accounts.helper import send_message
import logging
from import_export.admin import ImportExportModelAdmin
from import_export import resources

logger = logging.getLogger(__name__)

class PaymentMethodInline(admin.TabularInline):
    model = PaymentMethod
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['payment_type', 'amount', 'status', 'transaction_id', 'created_at', 'updated_at']

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        fields = ('order_number', 'user__phone_number', 'user__email', 'status', 'payment_status', 
                 'total_amount', 'discount_amount', 'final_amount', 'unpaid_amount',
                 'receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 
                 'receiver_postal_code', 'notes', 'tracking_code', 'created_at')
        export_order = fields

    def get_export_headers(self):
        headers = super().get_export_headers()
        # اضافه کردن هدرهای مربوط به روش‌های پرداخت
        headers.extend([
            'روش پرداخت کیف پول',
            'مبلغ پرداختی کیف پول',
            'وضعیت پرداخت کیف پول',
            'روش پرداخت درگاه',
            'مبلغ پرداختی درگاه',
            'وضعیت پرداخت درگاه',
            'شماره تراکنش درگاه'
        ])
        return headers

    def export_obj(self, obj):
        data = super().export_obj(obj)
        # اضافه کردن اطلاعات روش‌های پرداخت
        wallet_payment = obj.payments.filter(payment_type='wallet').first()
        gateway_payment = obj.payments.filter(payment_type='gateway').first()
        
        data.update({
            'روش پرداخت کیف پول': wallet_payment.get_payment_type_display() if wallet_payment else '',
            'مبلغ پرداختی کیف پول': wallet_payment.amount if wallet_payment else '',
            'وضعیت پرداخت کیف پول': wallet_payment.get_status_display() if wallet_payment else '',
            'روش پرداخت درگاه': gateway_payment.get_payment_type_display() if gateway_payment else '',
            'مبلغ پرداختی درگاه': gateway_payment.amount if gateway_payment else '',
            'وضعیت پرداخت درگاه': gateway_payment.get_status_display() if gateway_payment else '',
            'شماره تراکنش درگاه': gateway_payment.transaction_id if gateway_payment else ''
        })
        return data

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['total_price']
    fields = ['product', 'quantity', 'unit_price', 'total_price']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'changed_at', 'notes']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    resource_class = OrderResource
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 'final_amount_display', 'get_jalali_created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__phone_number', 'user__email']
    inlines = [OrderItemInline, OrderStatusHistoryInline, PaymentMethodInline]
    readonly_fields = ['order_number', 'get_jalali_created_at', 'get_jalali_updated_at', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'status', 'payment_status', 'total_amount', 'discount_amount', 'final_amount', 'unpaid_amount', 'reward_applied')
        }),
        ('اطلاعات گیرنده', {
            'fields': ('receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'receiver_postal_code')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('notes', 'tracking_code', 'get_jalali_created_at', 'get_jalali_updated_at')
        }),
    )

    def final_amount_display(self, obj):
        return format_html('<span style="direction:ltr">{}</span>', f"{obj.final_amount:,}")
    final_amount_display.short_description = "مبلغ نهایی (ریال)"

    def get_jalali_created_at(self, obj):
        return obj.get_jalali_created_at()
    get_jalali_created_at.short_description = 'تاریخ ثبت'

    def get_jalali_updated_at(self, obj):
        return obj.get_jalali_updated_at()
    get_jalali_updated_at.short_description = 'تاریخ بروزرسانی'

    def save_model(self, request, obj, form, change):
        if change:  # فقط برای به‌روزرسانی
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                # اگر وضعیت به shipped تغییر کرده باشد
                if old_obj.status != 'shipped' and obj.status == 'shipped':
                    # ارسال پیامک به مشتری
                    message = f'.'
                    send_message(
                        obj.user.phone_number,
                        message,
                        template='order-send-confirmation'
                    )
                    logger.info(f"📤 پیامک ارسال سفارش برای {obj.order_number} ارسال شد")
            except Order.DoesNotExist:
                pass
        
        if change and 'status' in form.changed_data:
            OrderStatusHistory.objects.create(
                order=obj,
                old_status=form.initial['status'],
                new_status=obj.status,
                changed_by=request.user
            )
        super().save_model(request, obj, form, change)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price_display', 'total_price_display']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['total_price']

    def unit_price_display(self, obj):
        return f"{obj.unit_price:,}"
    unit_price_display.short_description = "قیمت واحد (ریال)"

    def total_price_display(self, obj):
        return f"{obj.total_price:,}"
    total_price_display.short_description = "قیمت کل (ریال)"

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