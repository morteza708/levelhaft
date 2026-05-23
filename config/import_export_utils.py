"""
ابزارهای مشترک import/export پنل ادمین.
- export: XLSX و CSV فارسی
- import امن: فقط به‌روزرسانی رکورد موجود (فاز ۲+)
"""
from import_export import resources
from import_export.admin import ExportMixin, ImportExportModelAdmin
from import_export.formats import base_formats
from import_export import widgets
from import_export.results import RowResult
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist


class PersianCSV(base_formats.CSV):
    """CSV با BOM برای باز شدن درست فارسی در Excel ویندوز."""

    def export_data(self, dataset, **kwargs):
        return dataset.export('csv', encoding='utf-8-sig')


class PersianXLSX(base_formats.XLSX):
    """خروجی Excel واقعی (xlsx)."""

    def get_extension(self):
        return 'xlsx'


EXPORT_FORMATS = (PersianXLSX, PersianCSV)
IMPORT_FORMATS = EXPORT_FORMATS


def bool_fa(value):
    return 'بله' if value else 'خیر'


def normalize_digits(value):
    if value is None:
        return ''
    persian = '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩'
    english = '01234567890123456789'
    return str(value).strip().translate(str.maketrans(persian, english))


def parse_bool_fa(value):
    if value is None or value == '':
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in ('بله', 'yes', 'true', '1', 'y'):
        return True
    if normalized in ('خیر', 'no', 'false', '0', 'n'):
        return False
    return None


class BooleanFaWidget(widgets.BooleanWidget):
    def clean(self, value, row=None, **kwargs):
        parsed = parse_bool_fa(value)
        if parsed is None and value not in (None, ''):
            raise ValueError(f'مقدار بولی نامعتبر: {value}')
        return parsed


class GenderFaWidget(widgets.Widget):
    MAP = {
        'مرد': 'male',
        'زن': 'female',
        'male': 'male',
        'female': 'female',
    }

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return None
        key = str(value).strip()
        if key not in self.MAP:
            raise ValueError(f'جنسیت نامعتبر: {value}')
        return self.MAP[key]


class ChoiceFaWidget(widgets.Widget):
    """نگاشت برچسب فارسی (یا کد انگلیسی) به مقدار ذخیره‌شده در مدل."""

    def __init__(self, choices_map, *args, **kwargs):
        self.choices_map = choices_map
        super().__init__(*args, **kwargs)

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return None
        key = str(value).strip()
        if key not in self.choices_map:
            allowed = '، '.join(sorted(set(self.choices_map.keys())))
            raise ValueError(f'مقدار «{value}» نامعتبر است. مقادیر مجاز: {allowed}')
        return self.choices_map[key]


WORKSHOP_STATUS_WIDGET = ChoiceFaWidget({
    'در انتظار تایید': 'pending',
    'تایید شده': 'approved',
    'رد شده': 'rejected',
    'pending': 'pending',
    'approved': 'approved',
    'rejected': 'rejected',
})


class ExportOnlyModelAdmin(ExportMixin, admin.ModelAdmin):
    """فقط export — سفارش‌ها و گزارش تخفیف."""

    formats = EXPORT_FORMATS

    def has_import_permission(self, request):
        return False

    def get_import_formats(self):
        return []


class SafeImportExportModelAdmin(ImportExportModelAdmin):
    """import و export با فرمت‌های فارسی."""

    formats = EXPORT_FORMATS

    def get_import_formats(self):
        return list(IMPORT_FORMATS)

    def get_export_formats(self):
        return list(EXPORT_FORMATS)


class BaseExportResource(resources.ModelResource):
    """Resource پایه فقط برای export."""

    def import_data(self, *args, **kwargs):
        raise NotImplementedError('Import در این مدل فعال نیست.')


class SafeImportResource(resources.ModelResource):
    """
    import فقط به‌روزرسانی — رکورد جدید ساخته نمی‌شود.
    کلید شناسایی در Meta.import_id_fields تعریف شود.
    """

    class Meta:
        skip_unchanged = True
        report_skipped = True
        use_bulk = False

    def get_instance(self, instance_loader, row):
        instance = super().get_instance(instance_loader, row)
        if instance is None or instance.pk is None:
            raise ObjectDoesNotExist('رکورد برای به‌روزرسانی یافت نشد.')
        return instance

    def import_row(self, row, instance_loader, **kwargs):
        try:
            return super().import_row(row, instance_loader, **kwargs)
        except ObjectDoesNotExist:
            return RowResult(
                import_type=RowResult.IMPORT_TYPE_ERROR,
                errors=[f'رکورد با کلید «{self._row_id_display(row)}» در سیستم وجود ندارد.'],
            )

    def _row_id_display(self, row):
        id_fields = getattr(self._meta, 'import_id_fields', ()) or ()
        parts = []
        for field_name in id_fields:
            column = self._meta.fields.get(field_name)
            header = column.column_name if column else field_name
            parts.append(f'{header}={row.get(header, row.get(field_name, ""))}')
        return ', '.join(parts) or 'نامشخص'
