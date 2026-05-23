# accounts/admin.py
from django.contrib import admin
from django.db import transaction
from import_export.fields import Field

from django.core.exceptions import ObjectDoesNotExist
from import_export.widgets import ForeignKeyWidget

from config.import_export_utils import (
    BooleanFaWidget,
    GenderFaWidget,
    SafeImportExportModelAdmin,
    SafeImportResource,
    bool_fa,
    normalize_digits,
)
from config.jalali import format_jalali_datetime

from .helper import send_message
from .models import CustomUser, CustomerProfile, Address


def convert_persian_to_english(text):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table)


class CustomUserResource(SafeImportResource):
    phone_number = Field(attribute='phone_number', column_name='شماره موبایل')
    first_name = Field(attribute='first_name', column_name='نام')
    last_name = Field(attribute='last_name', column_name='نام خانوادگی')
    email = Field(attribute='email', column_name='ایمیل')
    is_beautician = Field(
        attribute='is_beautician',
        column_name='بیوتیشن',
        widget=BooleanFaWidget(),
    )
    is_active = Field(
        attribute='is_active',
        column_name='فعال',
        widget=BooleanFaWidget(),
    )
    date_joined = Field(column_name='تاریخ عضویت')

    # فیلدهای ممنوع در import — هرگز از Excel ست نمی‌شوند
    BLOCKED_IMPORT_COLUMNS = frozenset({
        'رمز عبور', 'password', 'is_staff', 'is_superuser',
        'کارمند', 'مدیر کل', 'otp_code', 'کد تایید',
    })

    class Meta:
        model = CustomUser
        import_id_fields = ('phone_number',)
        fields = (
            'phone_number', 'first_name', 'last_name', 'email',
            'is_beautician', 'is_active',
        )
        export_order = (
            'phone_number', 'first_name', 'last_name', 'email',
            'is_beautician', 'is_active', 'date_joined',
        )

    def dehydrate_is_beautician(self, user):
        return bool_fa(user.is_beautician)

    def dehydrate_is_active(self, user):
        return bool_fa(user.is_active)

    def dehydrate_date_joined(self, user):
        return format_jalali_datetime(user.date_joined, fmt='%Y/%m/%d %H:%M')

    def before_import_row(self, row, **kwargs):
        for column in self.BLOCKED_IMPORT_COLUMNS:
            if column in row and row[column] not in (None, ''):
                raise ValueError(f'ستون «{column}» در import کاربران مجاز نیست.')
        phone = normalize_digits(row.get('شماره موبایل', ''))
        if not phone:
            raise ObjectDoesNotExist('شماره موبایل خالی است.')
        row['شماره موبایل'] = phone
        try:
            user = CustomUser.objects.get(phone_number=phone)
            row['_old_is_beautician'] = user.is_beautician
        except CustomUser.DoesNotExist:
            raise ObjectDoesNotExist(f'کاربر با موبایل {phone} یافت نشد.')
        super().before_import_row(row, **kwargs)

    def get_instance(self, instance_loader, row):
        instance = super().get_instance(instance_loader, row)
        if instance is None or instance.pk is None:
            raise ObjectDoesNotExist(f'کاربر با موبایل {row.get("شماره موبایل")} یافت نشد.')
        return instance

    def save_instance(self, instance, is_create, row, **kwargs):
        instance.is_staff = False
        instance.is_superuser = False
        super().save_instance(instance, is_create, row, **kwargs)

    def after_save_instance(self, instance, row, **kwargs):
        if kwargs.get('dry_run'):
            return
        if hasattr(instance, 'profile'):
            if instance.profile.is_beautician != instance.is_beautician:
                instance.profile.is_beautician = instance.is_beautician
                instance.profile.save(update_fields=['is_beautician'])
        old_beautician = row.get('_old_is_beautician')
        if old_beautician is False and instance.is_beautician:
            send_message(
                instance.phone_number,
                '.',
                template='beautician-congrats',
            )


class CustomerProfileResource(SafeImportResource):
    user = Field(
        attribute='user',
        column_name='شماره موبایل',
        widget=ForeignKeyWidget(CustomUser, 'phone_number'),
    )
    user_phone = Field(column_name='شماره موبایل')
    first_name = Field(attribute='first_name', column_name='نام')
    last_name = Field(attribute='last_name', column_name='نام خانوادگی')
    birth_date = Field(column_name='تاریخ تولد')
    age = Field(attribute='age', column_name='سن')
    gender = Field(attribute='gender', column_name='جنسیت', widget=GenderFaWidget())
    clinic_name = Field(attribute='clinic_name', column_name='نام کلینیک')
    activity_city = Field(attribute='activity_city', column_name='شهر فعالیت')
    activity_history = Field(attribute='activity_history', column_name='سابقه فعالیت')
    brand_used = Field(attribute='brand_used', column_name='برندهای استفاده‌شده')
    instagram_url = Field(attribute='instagram_url', column_name='اینستاگرام')
    is_beautician = Field(
        attribute='is_beautician',
        column_name='بیوتیشن',
        widget=BooleanFaWidget(),
    )

    class Meta:
        model = CustomerProfile
        import_id_fields = ('user',)
        fields = (
            'user', 'first_name', 'last_name', 'birth_date', 'age', 'gender',
            'clinic_name', 'activity_city', 'activity_history', 'brand_used',
            'instagram_url', 'is_beautician',
        )
        export_order = (
            'user_phone', 'first_name', 'last_name', 'birth_date', 'age', 'gender',
            'clinic_name', 'activity_city', 'activity_history', 'brand_used',
            'instagram_url', 'is_beautician',
        )

    def get_queryset(self):
        return super().get_queryset().select_related('user')

    def dehydrate_user_phone(self, profile):
        return profile.user.phone_number

    def dehydrate_birth_date(self, profile):
        return str(profile.birth_date) if profile.birth_date else ''

    def dehydrate_gender(self, profile):
        return profile.get_gender_display() if profile.gender else ''

    def dehydrate_is_beautician(self, profile):
        return bool_fa(profile.is_beautician)

    def before_import_row(self, row, **kwargs):
        phone = normalize_digits(row.get('شماره موبایل', ''))
        if phone:
            row['شماره موبایل'] = phone
        if not phone:
            raise ObjectDoesNotExist('شماره موبایل خالی است.')
        try:
            profile = CustomerProfile.objects.select_related('user').get(
                user__phone_number=phone,
            )
            row['_old_is_beautician'] = profile.is_beautician
        except CustomerProfile.DoesNotExist:
            raise ObjectDoesNotExist(f'پروفایل با موبایل {phone} یافت نشد.')
        super().before_import_row(row, **kwargs)

    def after_save_instance(self, instance, row, **kwargs):
        if kwargs.get('dry_run'):
            return
        old_beautician = row.get('_old_is_beautician')
        if old_beautician is False and instance.is_beautician:
            if not instance.user.is_beautician:
                instance.user.is_beautician = True
                instance.user.save(update_fields=['is_beautician'])
                send_message(
                    instance.user.phone_number,
                    '.',
                    template='beautician-congrats',
                )
        elif instance.user.is_beautician != instance.is_beautician:
            instance.user.is_beautician = instance.is_beautician
            instance.user.save(update_fields=['is_beautician'])

    def get_instance(self, instance_loader, row):
        instance = super().get_instance(instance_loader, row)
        if instance is None or instance.pk is None:
            raise ObjectDoesNotExist(f'پروفایل با موبایل {row.get("شماره موبایل")} یافت نشد.')
        return instance


class CustomUserAdmin(SafeImportExportModelAdmin):
    resource_class = CustomUserResource
    list_display = ('phone_number', 'first_name', 'last_name', 'email', 'is_beautician')
    actions = ['make_beautician']
    search_fields = ['phone_number', 'first_name', 'last_name']

    def has_import_permission(self, request):
        return request.user.is_superuser

    def make_beautician(self, request, queryset):
        with transaction.atomic():
            users = list(queryset)
            for user in users:
                user.is_beautician = True
            CustomUser.objects.bulk_update(users, ['is_beautician'])
            for user in users:
                send_message(user.phone_number, '.', template='beautician-congrats')
    make_beautician.short_description = 'تبدیل به بیوتیشن'

    def get_search_results(self, request, queryset, search_term):
        search_term_en = convert_persian_to_english(search_term)
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term_en.isdigit():
            queryset |= self.model.objects.filter(phone_number__icontains=search_term_en)
        return queryset, use_distinct


class CustomerProfileAdmin(SafeImportExportModelAdmin):
    resource_class = CustomerProfileResource
    list_display = ('user_fa', 'first_name', 'last_name', 'clinic_name', 'is_beautician_fa')
    fields = (
        'user', 'first_name', 'last_name', 'birth_date', 'age', 'gender', 'clinic_name',
        'activity_city', 'activity_history', 'brand_used', 'instagram_url', 'is_beautician',
    )
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
                send_message(profile.user.phone_number, '.', template='beautician-congrats')
        self.message_user(request, 'پروفایل‌ها به بیوتیشن تبدیل شدند.')
    make_beautician.short_description = 'تبدیل به بیوتیشن'

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            if change:
                old_obj = self.model.objects.get(pk=obj.pk)
                if not old_obj.is_beautician and obj.is_beautician:
                    super().save_model(request, obj, form, change)
                    obj.user.is_beautician = True
                    obj.user.save()
                    send_message(obj.user.phone_number, '.', template='beautician-congrats')
                    self.message_user(request, 'کاربر به بیوتیشن تبدیل شد و پیام تبریک ارسال شد.')
                else:
                    super().save_model(request, obj, form, change)
                    obj.user.is_beautician = obj.is_beautician
                    obj.user.save()
            else:
                super().save_model(request, obj, form, change)
                obj.user.is_beautician = obj.is_beautician
                obj.user.save()

    def get_search_results(self, request, queryset, search_term):
        search_term_en = convert_persian_to_english(search_term)
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term_en.isdigit():
            queryset |= self.model.objects.filter(user__phone_number__icontains=search_term_en)
        return queryset, use_distinct


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(Address)
