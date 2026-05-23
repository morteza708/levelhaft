import math
from dataclasses import dataclass

import jdatetime
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import BusinessDiscount, DiscountUsage


@dataclass
class DiscountResult:
    discount: BusinessDiscount
    discount_amount: int


def _normalize_code(code):
    return (code or '').strip().upper()


def _user_is_beautician(user):
    if not user.is_authenticated:
        return False
    if getattr(user, 'is_beautician', False):
        return True
    return hasattr(user, 'profile') and user.profile.is_beautician


def validate_and_calculate_discount(code, user, cart_total):
    normalized_code = _normalize_code(code)
    if not normalized_code:
        raise ValidationError('لطفاً کد تخفیف را وارد کنید.')

    if cart_total <= 0:
        raise ValidationError('مبلغ سبد خرید برای اعمال تخفیف معتبر نیست.')

    try:
        discount = BusinessDiscount.objects.get(code=normalized_code)
    except BusinessDiscount.DoesNotExist:
        raise ValidationError('کد تخفیف وارد شده معتبر نیست.')

    if not discount.is_active:
        raise ValidationError('این کد تخفیف غیرفعال است.')

    if discount.usage_limit <= 0:
        raise ValidationError('ظرفیت استفاده از این کد تخفیف تمام شده است.')

    today = jdatetime.date.today()
    if discount.start_date and today < discount.start_date:
        raise ValidationError('زمان استفاده از این کد تخفیف هنوز فرا نرسیده است.')
    if discount.end_date and today > discount.end_date:
        raise ValidationError('مهلت استفاده از این کد تخفیف به پایان رسیده است.')

    is_beautician = _user_is_beautician(user)
    if is_beautician and not discount.allow_beauticians:
        raise ValidationError('این کد تخفیف برای کاربران بیوتیشن فعال نیست.')
    if not is_beautician and not discount.allow_regular_users:
        raise ValidationError('این کد تخفیف برای کاربران عادی فعال نیست.')

    if DiscountUsage.objects.filter(discount=discount, user=user).exists():
        raise ValidationError('شما قبلاً از این کد تخفیف استفاده کرده‌اید.')

    discount_amount = _calculate_discount_amount(discount, cart_total)
    if discount_amount <= 0:
        raise ValidationError('مبلغ تخفیف محاسبه‌شده معتبر نیست.')
    if discount_amount > cart_total:
        raise ValidationError('مبلغ تخفیف نمی‌تواند بیشتر از مبلغ سفارش باشد.')

    return DiscountResult(discount=discount, discount_amount=discount_amount)


def _calculate_discount_amount(discount, cart_total):
    if discount.percent:
        raw_amount = cart_total * discount.percent / 100
        discount_amount = math.ceil(raw_amount)
        if discount.max_discount_amount:
            discount_amount = min(discount_amount, discount.max_discount_amount)
        return discount_amount
    return min(discount.fixed_amount, cart_total)


@transaction.atomic
def consume_discount(discount, user, order, discount_amount):
    locked_discount = BusinessDiscount.objects.select_for_update().get(pk=discount.pk)

    if locked_discount.usage_limit <= 0:
        raise ValidationError('ظرفیت استفاده از این کد تخفیف تمام شده است.')

    DiscountUsage.objects.create(
        discount=locked_discount,
        user=user,
        order=order,
        amount=discount_amount,
    )

    locked_discount.usage_limit -= 1
    if locked_discount.usage_limit <= 0:
        locked_discount.is_active = False
    locked_discount.save(update_fields=['usage_limit', 'is_active', 'updated_at'])

    return locked_discount


@transaction.atomic
def release_discount_usage(order):
    try:
        usage = DiscountUsage.objects.select_related('discount').get(order=order)
    except DiscountUsage.DoesNotExist:
        return

    discount = BusinessDiscount.objects.select_for_update().get(pk=usage.discount_id)
    discount.usage_limit += 1
    discount.is_active = True
    discount._sync_auto_active_state()
    discount.save(update_fields=['usage_limit', 'is_active', 'updated_at'])
    usage.delete()
