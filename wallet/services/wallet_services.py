import math
from ..models import WalletTransaction
from django.db import models
from .sms_service import send_reward_sms

def withdraw_from_wallet(wallet, amount, description="برداشت از کیف پول"):
    if wallet.balance >= amount:
        wallet.balance -= amount
        wallet.save()
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            type='withdraw',
            description=description
        )
        return True
    return False

def deposit_to_wallet(wallet, amount, transaction_type='deposit', description="افزایش موجودی"):
    wallet.balance += amount
    wallet.save()
    WalletTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        type=transaction_type,
        description=description
    )

def apply_order_reward(order):
    user = order.user
    wallet = user.wallet

    # جلوگیری از اعمال پاداش در صورت لغو یا اعمال‌شده بودن
    if order.status == 'cancelled':
        return

    if order.reward_applied:
        return

    # مجموع خریدهای قبلی (بدون این سفارش)
    total_spent_before = user.orders.filter(
        payment_status='paid'
    ).exclude(id=order.id).aggregate(
        models.Sum('total_amount')
    )['total_amount__sum'] or 0

    total_spent = total_spent_before + order.total_amount

    if user.profile.is_beautician:
        if total_spent < 200_000_000:
            percent = 0.05
        elif total_spent < 400_000_000:
            percent = 0.08
        else:
            percent = 0.10
    else:
        percent = 0.03

    reward = math.ceil(order.total_amount * percent)

    # واریز به کیف پول
    deposit_to_wallet(wallet, reward, transaction_type='reward', description=f"پاداش سفارش {order.order_number}")

    # ارسال پیامک پاداش
    send_reward_sms(user, reward, order.order_number)

    # علامت‌گذاری سفارش به‌عنوان پاداش داده‌شده
    order.reward_applied = True
    order.save()


# def apply_order_reward(order):
#     user = order.user
#     wallet = user.wallet
#     # مجموع خریدهای قبلی (بدون سفارش فعلی) فقط سفارش‌های پرداخت شده
#     total_spent_before = user.orders.filter(
#         payment_status='paid'
#     ).exclude(id=order.id).aggregate(
#         models.Sum('total_amount')
#     )['total_amount__sum'] or 0
#     # مجموع جدید با احتساب این سفارش
#     total_spent = total_spent_before + order.total_amount

#     if user.profile.is_beautician:
#         if total_spent < 200_000_000:
#             percent = 0.05
#         elif total_spent < 400_000_000:
#             percent = 0.08
#         else:
#             percent = 0.10
#     else:
#         percent = 0.03

#     reward = math.ceil(order.total_amount * percent)
#     deposit_to_wallet(wallet, reward, transaction_type='reward', description=f"پاداش سفارش {order.order_number}")


def get_order_reward_amount(order):
    user = order.user
    total_spent_before = user.orders.filter(
        payment_status='paid'
    ).exclude(id=order.id).aggregate(
        models.Sum('total_amount')
    )['total_amount__sum'] or 0

    total_spent = total_spent_before + order.total_amount

    if user.profile.is_beautician:
        if total_spent < 200_000_000:
            percent = 0.05
        elif total_spent < 400_000_000:
            percent = 0.08
        else:
            percent = 0.10
    else:
        percent = 0.03

    return math.ceil(order.total_amount * percent)
