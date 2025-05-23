from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory
from accounts.tasks import send_message_task
import logging
from import_export.admin import ImportExportModelAdmin
from import_export import resources

logger = logging.getLogger(__name__)

class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        fields = ('order_number', 'user__phone_number', 'user__email', 'status', 'payment_status', 
                 'total_amount', 'discount_amount', 'final_amount', 'unpaid_amount',
                 'receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 
                 'receiver_postal_code', 'notes', 'tracking_code', 'created_at')
        export_order = fields

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
        'order_number', 'user', 'status', 'payment_status', 'final_amount_display', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__phone_number', 'user__email']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at']

    def final_amount_display(self, obj):
        return format_html('<span style="direction:ltr">{}</span>', f"{obj.final_amount:,}")
    final_amount_display.short_description = "مبلغ نهایی (ریال)"

    def save_model(self, request, obj, form, change):
        if change:  # فقط برای به‌روزرسانی
            try:
                old_obj = Order.objects.get(pk=obj.pk)
                # اگر وضعیت به shipped تغییر کرده باشد
                if old_obj.status != 'shipped' and obj.status == 'shipped':
                    # ارسال پیامک به مشتری
                    message = f'.'
                    send_message_task.delay(
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
    list_display = ['order', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['created_at']
    search_fields = ['order__order_number', 'product__name']
    readonly_fields = ['total_price']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'old_status', 'new_status', 'changed_by', 'get_jalali_changed_at']
    list_filter = ['changed_at']
    search_fields = ['order__order_number']
    readonly_fields = ['changed_at', 'changed_by'] 