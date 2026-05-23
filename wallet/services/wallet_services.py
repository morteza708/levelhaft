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

def get_order_reward_amount(order, gateway_amount=None):
    """
    محاسبه پاداش سفارش بر اساس مبلغ پرداخت شده از درگاه
    """
    user = order.user
    
    # اگر gateway_amount مشخص نشده، محاسبه کن
    if gateway_amount is None:
        gateway_payment = order.payments.filter(
            payment_type='gateway', 
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        gateway_amount = gateway_payment
    
    # اگر مبلغ درگاه صفر باشد، پاداش صفر
    if gateway_amount == 0:
        return 0
    
    # پاداش خرید (کش‌بک) غیرفعال است
    return 0

def apply_order_reward(order):
    """
    اعمال پاداش سفارش بر اساس مبلغ پرداخت شده از درگاه
    """
    user = order.user
    wallet = user.wallet

    # جلوگیری از اعمال پاداش در صورت لغو یا اعمال‌شده بودن
    if order.status == 'cancelled':
        return

    if order.reward_applied:
        return

    # محاسبه مبلغ پرداخت شده از درگاه
    gateway_payment = order.payments.filter(
        payment_type='gateway', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    # اگر مبلغ درگاه صفر باشد، پاداش اعمال نشود
    if gateway_payment == 0:
        return

    # محاسبه پاداش بر اساس مبلغ درگاه
    reward = get_order_reward_amount(order, gateway_payment)
    
    # اگر پاداش صفر باشد، اعمال نشود
    if reward == 0:
        return

    # واریز به کیف پول
    deposit_to_wallet(wallet, reward, transaction_type='reward', 
                     description=f"پاداش سفارش {order.order_number}")

    # ارسال پیامک پاداش
    send_reward_sms(user, reward, order.order_number)

    # علامت‌گذاری سفارش به‌عنوان پاداش داده‌شده
    order.reward_applied = True
    order.save(update_fields=["reward_applied"])
