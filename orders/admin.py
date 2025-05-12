from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory
from accounts.tasks import send_message_task
import logging

logger = logging.getLogger(__name__)

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
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'final_amount', 'get_jalali_created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__first_name', 'user__last_name', 'receiver_name', 'receiver_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'get_jalali_created_at', 'get_jalali_updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('اطلاعات مالی', {
            'fields': ('total_amount', 'discount_amount', 'final_amount')
        }),
        ('اطلاعات گیرنده', {
            'fields': ('receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'receiver_postal_code')
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('notes', 'tracking_code', 'created_at', 'updated_at', 'get_jalali_created_at', 'get_jalali_updated_at')
        }),
    )

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