from django.contrib import admin
from django.http import HttpResponse
from .models import (
    Brand, Line, UsageType, ProductModel, SkinType,
    SkinCondition, VolumeUnit, Product, ProductImage, Comment
)
from django.utils.html import format_html
from .forms import ProductForm, ProductAdminForm
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .utils import convert_to_english_digits

def format_price(value):
    if value is not None:
        return f"{int(value):,} ریال"
    return "-"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('barcode', 'name', 'brand__name', 'line__name', 'usage_type__name', 
                 'model__name', 'volume_value', 'volume_unit__name', 'short_description',
                 'price_level_1', 'price_level_2', 'stock', 'is_featured', 'show_on_home',
                 'created_at')
        export_order = fields

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_image', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "بدون تصویر"
    display_image.short_description = "لوگو"

@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand')
    list_filter = ('brand',)
    search_fields = ('name', 'brand__name', 'slug')

@admin.register(UsageType)
class UsageTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(ProductModel)
class ProductModelAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(SkinType)
class SkinTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(SkinCondition)
class SkinConditionAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(VolumeUnit)
class VolumeUnitAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    form = ProductAdminForm
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'brand', 'line', 'usage_type', 'formatted_price_1', 'formatted_price_2', 'stock', 'is_featured', 'show_on_home',)
    list_filter = ('brand', 'line', 'usage_type', 'model', 'skin_types', 'skin_conditions', 'is_featured', 'show_on_home')
    search_fields = ('name', 'barcode')
    list_editable = ('is_featured', 'show_on_home', 'stock')
    autocomplete_fields = ['brand', 'line', 'usage_type', 'model', 'volume_unit', 'skin_types', 'skin_conditions']
    inlines = [ProductImageInline]
    filter_horizontal = ('skin_types', 'skin_conditions')
    actions = ['make_featured']

    class Media:
        js = ('js/price-format.js',)

    def formatted_price_1(self, obj):
        return format_price(obj.price_level_1)
    formatted_price_1.short_description = "قیمت بیوتیشن"

    def formatted_price_2(self, obj):
        return format_price(obj.price_level_2)
    formatted_price_2.short_description = "قیمت عادی"

    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} محصول به عنوان محصول ویژه علامت‌گذاری شد.")
    make_featured.short_description = "علامت‌گذاری به عنوان محصول ویژه"

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    list_filter = ('product',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_link', 'rating_stars', 'status_badge', 'created_at', 'action_buttons')
    list_filter = ('status', 'rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'text')
    list_per_page = 20
    actions = ['approve_comments', 'reject_comments']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'user', 'text', 'rating')
        }),
        ('وضعیت', {
            'fields': ('status',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def product_link(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_link.short_description = 'محصول'

    def rating_stars(self, obj):
        stars = ''.join(['★' if i <= obj.rating else '☆' for i in range(1, 6)])
        return format_html('<span style="color: gold; font-size: 16px;">{}</span>', stars)
    rating_stars.short_description = 'امتیاز'

    def status_badge(self, obj):
        status_colors = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        status_texts = {
            'pending': 'در انتظار تایید',
            'approved': 'تایید شده',
            'rejected': 'رد شده'
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, status_texts.get(obj.status, obj.status)
        )
    status_badge.short_description = 'وضعیت'

    def action_buttons(self, obj):
        approve_url = reverse('products:admin_approve_comment', args=[obj.id])
        reject_url = reverse('products:admin_reject_comment', args=[obj.id])
        return format_html(
            '<a href="{}" class="btn btn-success btn-sm">تایید</a> '
            '<a href="{}" class="btn btn-danger btn-sm">--رد</a>',
            approve_url, reject_url
        )
    action_buttons.short_description = 'عملیات'

    def approve_comments(self, request, queryset):
        queryset.update(status='approved')
    approve_comments.short_description = 'تایید نظرات انتخاب شده'

    def reject_comments(self, request, queryset):
        queryset.update(status='rejected')
    reject_comments.short_description = 'رد نظرات انتخاب شده'

    class Media:
        css = {
            'all': ('admin/css/comment_admin.css',)
        }