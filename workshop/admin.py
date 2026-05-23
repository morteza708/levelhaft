from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from import_export.fields import Field

from accounts.helper import send_message
from config.import_export_utils import (
    SafeImportExportModelAdmin,
    SafeImportResource,
    WORKSHOP_STATUS_WIDGET,
    normalize_digits,
)
from config.jalali import format_jalali_datetime

from .models import (
    Workshop,
    WorkshopBrand,
    WorkshopRegistration,
    WorkshopRegistrationHistory,
)


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


class WorkshopRegistrationResource(SafeImportResource):
    user_phone = Field(column_name='شماره موبایل')
    user_name = Field(column_name='نام کاربر')
    workshop_title = Field(column_name='ورکشاپ')
    workshop_brand = Field(column_name='برند')
    barcode = Field(attribute='barcode', column_name='بارکد')
    first_name_en = Field(attribute='first_name_en', column_name='نام انگلیسی')
    last_name_en = Field(attribute='last_name_en', column_name='نام خانوادگی انگلیسی')
    clinic_name = Field(attribute='clinic_name', column_name='کلینیک')
    city = Field(attribute='city', column_name='شهر')
    address = Field(attribute='address', column_name='آدرس')
    status = Field(attribute='status', column_name='وضعیت', widget=WORKSHOP_STATUS_WIDGET)
    created_at = Field(column_name='تاریخ ثبت')

    class Meta:
        model = WorkshopRegistration
        import_id_fields = ('barcode',)
        fields = (
            'barcode', 'first_name_en', 'last_name_en', 'clinic_name',
            'city', 'address', 'status',
        )
        export_order = (
            'barcode', 'user_phone', 'user_name', 'workshop_title', 'workshop_brand',
            'first_name_en', 'last_name_en', 'clinic_name', 'city', 'address',
            'status', 'created_at',
        )

    def __init__(self, user=None, **kwargs):
        self.import_user = user
        super().__init__(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_related('user', 'workshop', 'workshop__brand')

    def dehydrate_user_phone(self, obj):
        return obj.user.phone_number

    def dehydrate_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.phone_number

    def dehydrate_workshop_title(self, obj):
        return obj.workshop.title

    def dehydrate_workshop_brand(self, obj):
        return obj.workshop.brand.name

    def dehydrate_status(self, obj):
        return obj.get_status_display()

    def dehydrate_created_at(self, obj):
        return format_jalali_datetime(obj.created_at, fmt='%Y/%m/%d %H:%M')

    def before_import_row(self, row, **kwargs):
        barcode = normalize_digits(row.get('بارکد', ''))
        if not barcode:
            raise ObjectDoesNotExist('بارکد خالی است.')
        row['بارکد'] = barcode
        try:
            registration = WorkshopRegistration.objects.select_related('user').get(
                barcode=barcode,
            )
            row['_old_status'] = registration.status
        except WorkshopRegistration.DoesNotExist:
            raise ObjectDoesNotExist(f'ثبت‌نام با بارکد {barcode} یافت نشد.')
        super().before_import_row(row, **kwargs)

    def get_instance(self, instance_loader, row):
        instance = super().get_instance(instance_loader, row)
        if instance is None or instance.pk is None:
            raise ObjectDoesNotExist(f'ثبت‌نام با بارکد {row.get("بارکد")} یافت نشد.')
        return instance

    def after_save_instance(self, instance, row, **kwargs):
        if kwargs.get('dry_run'):
            return
        old_status = row.get('_old_status')
        new_status = instance.status
        if old_status == new_status:
            return
        WorkshopRegistrationHistory.objects.create(
            registration=instance,
            old_status=old_status,
            new_status=new_status,
            changed_by=self.import_user,
        )
        if old_status != 'approved' and new_status == 'approved':
            send_message(
                instance.user.phone_number,
                instance.barcode,
                template='workshop-verification',
            )


@admin.register(WorkshopRegistration)
class WorkshopRegistrationAdmin(SafeImportExportModelAdmin):
    resource_class = WorkshopRegistrationResource
    list_display = ['full_name', 'workshop', 'status', 'barcode', 'get_jalali_created_at']
    list_filter = ['status', 'workshop__brand', 'city']
    search_fields = ['user__first_name', 'user__last_name', 'first_name_en', 'last_name_en', 'barcode']
    readonly_fields = ['barcode', 'created_at']
    autocomplete_fields = ['user', 'workshop']

    def get_import_resource_kwargs(self, request, *args, **kwargs):
        return {'user': request.user}

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
                send_message(obj.user.phone_number, obj.barcode, template='workshop-verification')
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
