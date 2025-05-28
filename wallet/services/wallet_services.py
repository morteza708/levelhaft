import math
from ..models import WalletTransaction, Wallet
from django.db import models, transaction
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

def apply_order_reward(user, amount, order_number):
    """اعمال پاداش خرید به کیف پول"""
    with transaction.atomic():
        wallet, created = Wallet.objects.get_or_create(user=user)
        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            type='reward',
            description=f'پاداش خرید سفارش {order_number}'
        )
        wallet.balance += amount
        wallet.save()
        
        # ارسال پیامک پاداش
        send_reward_sms(user.phone_number, amount)
        
        return transaction
