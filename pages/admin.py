from django.contrib import admin
from .models import ContactMessage, SliderSlide
from config.jalali import format_jalali_datetime
from django.utils.html import format_html
from django.utils.safestring import mark_safe

@admin.register(SliderSlide)
class SliderSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'link_display', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'link_type', 'created_at')
    search_fields = ('title', 'link_url')
    list_editable = ('is_active', 'order')
    ordering = ('order', '-created_at')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'image', 'image_mobile', 'is_active', 'order')
        }),
        ('تنظیمات لینک', {
            'fields': ('link_type', 'link_url'),
            'description': mark_safe('''
                <div style="background: #f0f6fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-right: 4px solid #28a745;">
                    <h4 style="margin-top: 0; color: #28a745;">📌 راهنمای وارد کردن لینک:</h4>
                    <p><strong>نوع لینک: URL کامل</strong></p>
                    <ul style="margin-bottom: 10px;">
                        <li>برای لینک‌های خارجی یا داخلی با آدرس کامل</li>
                        <li>مثال: <code>https://levelhaft.com/workshop/14/</code></li>
                        <li>مثال: <code>https://google.com</code></li>
                    </ul>
                    <p><strong>نوع لینک: نام URL Pattern</strong></p>
                    <ul style="margin-bottom: 0;">
                        <li>برای لینک‌های داخلی سایت با استفاده از نام URL pattern</li>
                        <li>فرمت: <code>app_name:url_name</code></li>
                        <li>مثال: <code>products:consult</code></li>
                        <li>مثال: <code>workshop:approved_registrations</code></li>
                        <li>مثال: <code>pages:home</code></li>
                    </ul>
                    <p style="margin-top: 10px; margin-bottom: 0;"><strong>⚠️ نکته:</strong> اگر لینک خالی باشد، به صورت پیش‌فرض # قرار می‌گیرد.</p>
                </div>
            ''')
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "پیش‌نمایش تصویر"
    
    def link_display(self, obj):
        if not obj.link_url:
            return format_html('<span style="color: #999;"># (پیش‌فرض)</span>')
        link_type_display = dict(obj.LINK_TYPE_CHOICES).get(obj.link_type, obj.link_type)
        return format_html('<strong>{}</strong>: {}', link_type_display, obj.link_url[:50])
    link_display.short_description = "لینک"

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at_jalali", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at", "created_at_jalali")
    ordering = ("-created_at",)

    def created_at_jalali(self, obj):
        return format_jalali_datetime(obj.created_at, fmt='%Y/%m/%d - %H:%M')
    created_at_jalali.short_description = "تاریخ ارسال"
