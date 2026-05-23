from urllib.parse import urlencode

from django.contrib import admin
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from jalali_date.admin import ModelAdminJalaliMixin
from config.jalali import format_jalali_datetime

from .models import BusinessDiscount, DiscountUsage
from .report_export import discount_report_excel_response
from .report_services import (
    apply_report_filters,
    build_code_summary,
    build_representative_summary,
    build_totals,
    get_filter_options,
    get_valid_report_usages,
    paginate_order_details,
)


class DiscountUsageInline(admin.TabularInline):
    model = DiscountUsage
    extra = 0
    readonly_fields = ['user', 'order', 'amount', 'created_at']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BusinessDiscount)
class BusinessDiscountAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = [
        'code',
        'title',
        'sales_representative',
        'discount_type_badge',
        'usage_limit',
        'is_active',
        'jalali_start_date',
        'jalali_end_date',
    ]
    list_filter = ['is_active', 'allow_regular_users', 'allow_beauticians', 'start_date', 'end_date']
    search_fields = ['code', 'title', 'sales_representative']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [DiscountUsageInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'sales_representative',
                'title',
                'code',
                'usage_limit',
                'is_active',
            ),
        }),
        ('نوع تخفیف', {
            'fields': ('percent', 'max_discount_amount', 'fixed_amount'),
            'description': 'فقط یکی از درصد یا مبلغ ثابت را پر کنید. برای درصدی، سقف الزامی است.',
        }),
        ('بازه زمانی', {
            'fields': ('start_date', 'end_date'),
        }),
        ('مخاطبان', {
            'fields': ('allow_regular_users', 'allow_beauticians'),
        }),
        ('زمان‌بندی سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def discount_type_badge(self, obj):
        return obj.discount_type_display
    discount_type_badge.short_description = 'نوع تخفیف'

    def jalali_start_date(self, obj):
        if obj.start_date:
            return obj.start_date.strftime('%Y/%m/%d')
        return '-'
    jalali_start_date.short_description = 'شروع'

    def jalali_end_date(self, obj):
        if obj.end_date:
            return obj.end_date.strftime('%Y/%m/%d')
        return '-'
    jalali_end_date.short_description = 'پایان'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'reports/',
                self.admin_site.admin_view(self.discount_reports_view),
                name='business_discounts_businessdiscount_reports',
            ),
            path(
                'reports/export/',
                self.admin_site.admin_view(self.discount_reports_export_view),
                name='business_discounts_businessdiscount_reports_export',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['discount_reports_url'] = reverse(
            'admin:business_discounts_businessdiscount_reports'
        )
        return super().changelist_view(request, extra_context=extra_context)

    def discount_reports_view(self, request):
        base_qs = get_valid_report_usages()
        filtered_qs = apply_report_filters(base_qs, request.GET)

        filter_params = {
            'q': request.GET.get('q', ''),
            'sales_representative': request.GET.get('sales_representative', ''),
            'discount_id': request.GET.get('discount_id', ''),
            'date_from': request.GET.get('date_from', ''),
            'date_to': request.GET.get('date_to', ''),
        }

        representatives, discounts = get_filter_options(base_qs)
        page_number = request.GET.get('page', 1)
        order_details_page, _paginator = paginate_order_details(filtered_qs, page_number)

        query_params = request.GET.copy()
        query_params.pop('page', None)
        query_string = urlencode(query_params, doseq=True)

        context = {
            **self.admin_site.each_context(request),
            'title': 'گزارش تخفیف‌های بیزنس',
            'filters': filter_params,
            'representatives': representatives,
            'discounts': discounts,
            'totals': build_totals(filtered_qs),
            'representative_summary': build_representative_summary(filtered_qs),
            'code_summary': build_code_summary(filtered_qs),
            'order_details_page': order_details_page,
            'query_string': query_string,
        }
        return render(request, 'admin/business_discounts/discount_reports.html', context)

    def discount_reports_export_view(self, request):
        return discount_report_excel_response(request)


@admin.register(DiscountUsage)
class DiscountUsageAdmin(admin.ModelAdmin):
    list_display = ['discount', 'user', 'order', 'amount_display', 'jalali_created_at']
    list_filter = ['created_at', 'discount']
    search_fields = ['discount__code', 'user__phone_number', 'order__order_number']
    readonly_fields = ['discount', 'user', 'order', 'amount', 'created_at']

    def amount_display(self, obj):
        return format_html('<span style="direction:ltr">{}</span>', f'{obj.amount:,}')
    amount_display.short_description = 'مبلغ تخفیف'

    def jalali_created_at(self, obj):
        return format_jalali_datetime(obj.created_at, fmt='%Y/%m/%d %H:%M')
    jalali_created_at.short_description = 'تاریخ مصرف'

    def has_add_permission(self, request):
        return False
