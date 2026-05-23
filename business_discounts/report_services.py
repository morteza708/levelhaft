from django.core.paginator import Paginator
from django.db.models import Avg, Count, Sum, Q
import jdatetime

from .models import BusinessDiscount, DiscountUsage


def _to_english_digits(value):
    translation_table = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    return str(value or '').translate(translation_table)


def parse_jalali_date(value):
    normalized = _to_english_digits(value).strip().replace('-', '/')
    if not normalized:
        return None

    try:
        year, month, day = [int(part) for part in normalized.split('/')]
        return jdatetime.date(year, month, day).togregorian()
    except (TypeError, ValueError):
        return None


def get_valid_report_usages():
    return DiscountUsage.objects.select_related(
        'discount',
        'user',
        'order',
    ).filter(
        order__payment_status='paid',
    ).exclude(
        order__status='cancelled',
    )


def apply_report_filters(queryset, params):
    search = (params.get('q') or '').strip()
    if search:
        queryset = queryset.filter(
            Q(discount__sales_representative__icontains=search)
            | Q(discount__code__icontains=search)
            | Q(discount__title__icontains=search)
            | Q(order__order_number__icontains=search)
            | Q(user__phone_number__icontains=search)
        )

    representative = (params.get('sales_representative') or '').strip()
    if representative:
        queryset = queryset.filter(discount__sales_representative=representative)

    discount_id = (params.get('discount_id') or '').strip()
    if discount_id.isdigit():
        queryset = queryset.filter(discount_id=int(discount_id))

    date_from = parse_jalali_date(params.get('date_from'))
    if date_from:
        queryset = queryset.filter(order__created_at__date__gte=date_from)

    date_to = parse_jalali_date(params.get('date_to'))
    if date_to:
        queryset = queryset.filter(order__created_at__date__lte=date_to)

    return queryset


def get_filter_options(queryset):
    representatives = (
        BusinessDiscount.objects.filter(
            id__in=queryset.values_list('discount_id', flat=True).distinct()
        )
        .values_list('sales_representative', flat=True)
        .distinct()
        .order_by('sales_representative')
    )
    discounts = (
        BusinessDiscount.objects.filter(
            id__in=queryset.values_list('discount_id', flat=True).distinct()
        )
        .order_by('-created_at')
        .values('id', 'code', 'title', 'sales_representative')
    )
    return list(representatives), list(discounts)


def build_representative_summary(queryset):
    rows = (
        queryset.values('discount__sales_representative')
        .annotate(
            codes_used=Count('discount_id', distinct=True),
            order_count=Count('id'),
            customer_count=Count('user_id', distinct=True),
            total_before_discount=Sum('order__total_amount'),
            total_discount=Sum('amount'),
            total_final=Sum('order__final_amount'),
        )
        .order_by('-total_final')
    )
    return [
        {
            'sales_representative': row['discount__sales_representative'],
            'codes_used': row['codes_used'] or 0,
            'order_count': row['order_count'] or 0,
            'customer_count': row['customer_count'] or 0,
            'total_before_discount': row['total_before_discount'] or 0,
            'total_discount': row['total_discount'] or 0,
            'total_final': row['total_final'] or 0,
        }
        for row in rows
    ]


def build_code_summary(queryset):
    rows = (
        queryset.values(
            'discount_id',
            'discount__code',
            'discount__title',
            'discount__sales_representative',
        )
        .annotate(
            order_count=Count('id'),
            customer_count=Count('user_id', distinct=True),
            total_before_discount=Sum('order__total_amount'),
            total_discount=Sum('amount'),
            total_final=Sum('order__final_amount'),
            avg_final=Avg('order__final_amount'),
        )
        .order_by('-total_final')
    )
    return [
        {
            'discount_id': row['discount_id'],
            'code': row['discount__code'],
            'title': row['discount__title'],
            'sales_representative': row['discount__sales_representative'],
            'order_count': row['order_count'] or 0,
            'customer_count': row['customer_count'] or 0,
            'total_before_discount': row['total_before_discount'] or 0,
            'total_discount': row['total_discount'] or 0,
            'total_final': row['total_final'] or 0,
            'avg_final': int(row['avg_final'] or 0),
        }
        for row in rows
    ]


def build_totals(queryset):
    agg = queryset.aggregate(
        order_count=Count('id'),
        customer_count=Count('user_id', distinct=True),
        total_before_discount=Sum('order__total_amount'),
        total_discount=Sum('amount'),
        total_final=Sum('order__final_amount'),
    )
    return {
        'order_count': agg['order_count'] or 0,
        'customer_count': agg['customer_count'] or 0,
        'total_before_discount': agg['total_before_discount'] or 0,
        'total_discount': agg['total_discount'] or 0,
        'total_final': agg['total_final'] or 0,
    }


def paginate_order_details(queryset, page_number, per_page=25):
    details_qs = queryset.order_by('-order__created_at')
    paginator = Paginator(details_qs, per_page)
    page = paginator.get_page(page_number)
    return page, paginator
