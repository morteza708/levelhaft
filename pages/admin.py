from django.contrib import admin
from .models import ContactMessage
from jalali_date import datetime2jalali

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at_jalali", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at", "created_at_jalali")
    ordering = ("-created_at",)

    def created_at_jalali(self, obj):
        return datetime2jalali(obj.created_at).strftime('%Y/%m/%d - %H:%M')
    created_at_jalali.short_description = "تاریخ ارسال"
