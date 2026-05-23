"""
تبدیل datetime به تاریخ/ساعت شمسی با timezone محلی پروژه (Asia/Tehran).
"""
import jdatetime
from django.utils import timezone


def format_jalali_datetime(value, fmt='%Y/%m/%d %H:%M:%S', empty='-'):
    """
    مقدار datetime را ابتدا به زمان محلی تبدیل می‌کند، سپس شمسی فرمت می‌کند.
    """
    if not value:
        return empty

    local_dt = timezone.localtime(value)
    return jdatetime.datetime.fromgregorian(datetime=local_dt).strftime(fmt)
