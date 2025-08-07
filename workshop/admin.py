from django.contrib import admin
from accounts.helper import send_message
from .models import Workshop, WorkshopBrand, WorkshopRegistration, WorkshopRegistrationHistory
from django.utils.html import format_html
from django.contrib import messages


@admin.register(WorkshopBrand)
class WorkshopBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand_logo']
    search_fields = ['name']
    
    def brand_logo(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 5px;" />', obj.image.url)
        return '-'
    brand_logo.short_description = 'لوگو برند'


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'date', 'city', 'display_price', 'capacity', 'workshop_image']
    list_filter = ['brand', 'city', 'date']
    search_fields = ['title', 'brand__name', 'city']
    readonly_fields = ['workshop_image_preview']
    
    def display_price(self, obj):
        return f"{int(obj.price):,} ریال"
    display_price.short_description = 'قیمت'
    
    def workshop_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return '-'
    workshop_image.short_description = 'تصویر'
    
    def workshop_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="400" style="border-radius: 10px;" />', obj.image.url)
        return '-'
    workshop_image_preview.short_description = 'پیش‌نمایش تصویر'

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'brand', 'date', 'city', 'capacity')
        }),
        ('اطلاعات مالی', {
            'fields': ('price',)
        }),
        ('محتوا', {
            'fields': ('description', 'image', 'workshop_image_preview')
        }),
    )


@admin.register(WorkshopRegistration)
class WorkshopRegistrationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'workshop', 'status', 'barcode', 'get_jalali_created_at']
    list_filter = ['status', 'workshop__brand', 'city']
    search_fields = ['user__first_name', 'user__last_name', 'first_name_en', 'last_name_en', 'barcode']
    readonly_fields = ['barcode', 'created_at']
    autocomplete_fields = ['user', 'workshop']
    
    def full_name(self, obj):
        return obj.user.get_full_name()
    full_name.short_description = 'نام و نام خانوادگی'
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': (('user', 'workshop'), ('first_name_en', 'last_name_en'))
        }),
        ('اطلاعات تماس و محل فعالیت', {
            'fields': ('clinic_name', 'city', 'address')
        }),
        ('وضعیت ثبت‌نام', {
            'fields': ('status', 'barcode', 'created_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            old_obj = self.model.objects.get(pk=obj.pk)
            if old_obj.status != 'approved' and obj.status == 'approved':
                super().save_model(request, obj, form, change)
                # ارسال پیامک به کاربر
                message = f"{obj.barcode}"
                send_message(obj.user.phone_number, message, template='workshop-verification')
                messages.success(request, f"پیامک تایید برای کاربر {obj.user.get_full_name()} ارسال شد.")
            else:
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'approved':
            return False
        return True


@admin.register(WorkshopRegistrationHistory)
class WorkshopRegistrationHistoryAdmin(admin.ModelAdmin):
    list_display = ['registration', 'display_user', 'display_workshop', 'old_status', 'new_status', 'get_jalali_changed_at', 'changed_by']
    list_filter = ['new_status', 'registration__workshop__brand', 'changed_at']
    search_fields = ['registration__user__first_name', 'registration__user__last_name', 'registration__workshop__title']
    readonly_fields = ['registration', 'old_status', 'new_status', 'changed_at', 'changed_by']
    
    def display_user(self, obj):
        return obj.registration.user.get_full_name()
    display_user.short_description = 'کاربر'
    
    def display_workshop(self, obj):
        return obj.registration.workshop.title
    display_workshop.short_description = 'ورکشاپ'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
