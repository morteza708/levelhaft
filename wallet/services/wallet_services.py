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

def get_order_reward_amount(order):
    user = order.user
    order_amount = order.total_amount

    if user.profile.is_beautician:
        if order_amount < 200_000_000:
            percent = 0.05
        elif order_amount < 400_000_000:
            percent = 0.08
        else:
            percent = 0.10
    else:
        percent = 0.03

    return math.ceil(order_amount * percent)

def apply_order_reward(order):
    user = order.user
    wallet = user.wallet

    # جلوگیری از اعمال پاداش در صورت لغو یا اعمال‌شده بودن
    if order.status == 'cancelled':
        return

    if order.reward_applied:
        return

    reward = get_order_reward_amount(order)

    # واریز به کیف پول
    deposit_to_wallet(wallet, reward, transaction_type='reward', 
                     description=f"پاداش سفارش {order.order_number}")

    # ارسال پیامک پاداش
    send_reward_sms(user, reward, order.order_number)

    # علامت‌گذاری سفارش به‌عنوان پاداش داده‌شده
    order.reward_applied = True
    order.save()
