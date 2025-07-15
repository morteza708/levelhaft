# accounts/admin.py
from django.contrib import admin
from django.db.models import Q
from django.db import transaction
from .models import CustomUser, CustomerProfile, Address
from .helper import send_message
from import_export.admin import ImportExportModelAdmin
from import_export import resources

def convert_persian_to_english(text):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table)

class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'first_name', 'last_name', 'email', 'is_beautician', 
                 'is_staff', 'is_superuser', 'is_active', 'date_joined')
        export_order = fields

class CustomerProfileResource(resources.ModelResource):
    class Meta:
        model = CustomerProfile
        fields = ('user__phone_number', 'first_name', 'last_name', 'birth_date', 'age', 
                 'gender', 'clinic_name', 'activity_city', 'activity_history', 
                 'brand_used', 'instagram_url', 'is_beautician')
        export_order = fields

class CustomUserAdmin(ImportExportModelAdmin):
    resource_class = CustomUserResource
    list_display = ('phone_number', 'first_name', 'last_name', 'email', 'is_beautician')
    actions = ['make_beautician']
    fields = ('phone_number', 'is_beautician', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser', 'is_active', 'password', 'permissions')
    search_fields = ['phone_number', 'first_name', 'last_name']

    def make_beautician(self, request, queryset):
        with transaction.atomic():  # استفاده از تراکنش
            # به‌روزرسانی گروهی کاربران
            users = list(queryset)
            for user in users:
                user.is_beautician = True
            CustomUser.objects.bulk_update(users, ['is_beautician'])  # ذخیره گروهی

            # ارسال پیامک مستقیم
            for user in users:
                message = f"."
                send_message(user.phone_number, message, template='beautician-congrats')
    make_beautician.short_description = "تبدیل به بیوتیشن"

    def get_search_results(self, request, queryset, search_term):
        # تبدیل شماره‌های فارسی به انگلیسی
        search_term_en = convert_persian_to_english(search_term)
        # جستجوی استاندارد با search_fields
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # اضافه کردن جستجوی سفارشی برای شماره تلفن تبدیل‌شده
        if search_term_en.isdigit():  # اگر ورودی فقط عدد باشد
            queryset |= self.model.objects.filter(phone_number__icontains=search_term_en)
        return queryset, use_distinct

class CustomerProfileAdmin(ImportExportModelAdmin):
    resource_class = CustomerProfileResource
    list_display = ('user_fa', 'first_name', 'last_name', 'clinic_name', 'is_beautician_fa')
    fields = ('user', 'first_name', 'last_name', 'birth_date', 'age', 'gender','clinic_name', 'activity_city', 'activity_history', 'brand_used','instagram_url', 'is_beautician')
    search_fields = ['first_name', 'last_name', 'user__phone_number']
    actions = ['make_beautician']

    def user_fa(self, obj):
        return obj.user
    user_fa.short_description = 'کاربر'

    def is_beautician_fa(self, obj):
        return obj.is_beautician
    is_beautician_fa.boolean = True
    is_beautician_fa.short_description = 'بیوتیشن'

    def make_beautician(self, request, queryset):
        with transaction.atomic():
            profiles = list(queryset)
            for profile in profiles:
                profile.is_beautician = True
            CustomerProfile.objects.bulk_update(profiles, ['is_beautician'])
            for profile in profiles:
                profile.user.is_beautician = True
            CustomUser.objects.bulk_update([profile.user for profile in profiles], ['is_beautician'])
            for profile in profiles:
                message = f"."
                send_message(profile.user.phone_number, message, template='beautician-congrats')
        self.message_user(request, "پروفایل‌ها به بیوتیشن تبدیل شدند.")
    make_beautician.short_description = "تبدیل به بیوتیشن"

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                old_obj = self.model.objects.get(pk=obj.pk)
                if not old_obj.is_beautician and obj.is_beautician:
                    super().save_model(request, obj, form, change)
                    obj.user.is_beautician = True
                    obj.user.save()
                    message = f"."
                    send_message(obj.user.phone_number, message, template='beautician-congrats')
                    self.message_user(request, "کاربر به بیوتیشن تبدیل شد و پیام تبریک ارسال شد.")
                else:
                    super().save_model(request, obj, form, change)
                    obj.user.is_beautician = obj.is_beautician
                    obj.user.save()
            else:
                super().save_model(request, obj, form, change)
                obj.user.is_beautician = obj.is_beautician
                obj.user.save()

    def get_search_results(self, request, queryset, search_term):
        # تبدیل شماره‌های فارسی به انگلیسی
        search_term_en = convert_persian_to_english(search_term)
        # جستجوی استاندارد با search_fields
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        # اضافه کردن جستجوی سفارشی برای شماره تلفن کاربر
        if search_term_en.isdigit():
            queryset |= self.model.objects.filter(user__phone_number__icontains=search_term_en)
        return queryset, use_distinct

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(Address)




