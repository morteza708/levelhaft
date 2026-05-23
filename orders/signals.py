from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import models
from .models import Order, PaymentMethod
from products.models import Product
from wallet.models import Wallet, WalletTransaction
from wallet.services.wallet_services import get_order_reward_amount, apply_order_reward
from business_discounts.services import release_discount_usage
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def test_order_signal(sender, instance, created, **kwargs):
    """سیگنال تست برای اطمینان از کارکرد سیگنال‌ها"""
    logger.info(f"🔔 سیگنال تست - سفارش {instance.order_number} {'ایجاد شد' if created else 'به‌روزرسانی شد'}")

@receiver(pre_save, sender=Order)
def handle_order_payment_pre_save(sender, instance, **kwargs):
    logger.info(f"🔍 بررسی تغییر وضعیت پرداخت برای سفارش {instance.order_number}")
    
    if not instance.pk:
        logger.info("سفارش جدید است")
        return  # سفارش جدید است
    try:
        old = sender.objects.get(pk=instance.pk)
        logger.info(f"وضعیت قبلی پرداخت: {old.payment_status}")
        logger.info(f"وضعیت جدید پرداخت: {instance.payment_status}")
    except sender.DoesNotExist:
        logger.info("سفارش قبلی یافت نشد")
        return

    if old.payment_status != 'paid' and instance.payment_status == 'paid':
        logger.info(f"🔄 تغییر وضعیت پرداخت به 'paid' برای سفارش {instance.order_number}")
        
        # کاهش موجودی محصولات فقط اگر payment_status از مقدار قبلی به 'paid' تغییر کند
        for item in instance.items.all():
            product = item.product
            product.stock -= item.quantity
            product.save()
            logger.info(f"[سیگنال سفارش] موجودی محصول {product.name} به میزان {item.quantity} کاهش یافت.")

@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    
    # ارسال پیامک هنگام تغییر وضعیت به "ارسال شده"
    if old.status != 'shipped' and instance.status == 'shipped':
        logger.info(f"🚚 تغییر وضعیت به 'shipped' برای سفارش {instance.order_number}")

@receiver(pre_save, sender=Order)
def handle_order_cancellation_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        return  # سفارش جدید است، نیازی به بررسی نیست

    try:
        old_order = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    # بررسی تغییر وضعیت به "لغو شده"
    if old_order.status != 'cancelled' and instance.status == 'cancelled':
        logger.info(f"📦 لغو سفارش: {instance.order_number}")

        # 1. بازگرداندن مصرف کد تخفیف
        release_discount_usage(instance)

        # 2. بازگرداندن موجودی کالاها
        for item in instance.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
            logger.info(f"✅ موجودی '{product.name}' افزایش یافت: +{item.quantity}")

        # 3. بازگشت مبالغ پرداخت‌شده (کیف پول و درگاه) به کیف پول
        payments = instance.payments.filter(status='completed')
        wallet = instance.user.wallet
        
        # محاسبه کل مبلغ پرداخت شده
        total_paid = sum(payment.amount for payment in payments)
        
        # اگر کل مبلغ سفارش پرداخت شده باشد، کل مبلغ را بازگردان
        if total_paid >= instance.final_amount:
            refund_amount = instance.final_amount
            
            # جلوگیری از واریز تکراری
            already_refunded = WalletTransaction.objects.filter(
                wallet=wallet,
                amount=refund_amount,
                type='deposit',
                description__icontains=f'بازگشت کل مبلغ سفارش لغو شده {instance.order_number}'
            ).exists()

            if not already_refunded:
                wallet.balance += refund_amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    type='deposit',
                    description=f'بازگشت کل مبلغ سفارش لغو شده {instance.order_number}'
                )
                logger.info(f"💰 کل مبلغ {refund_amount} ریال به کیف پول بازگردانده شد.")
        else:
            # بازگشت مبالغ پرداخت‌شده به صورت جداگانه
            for payment in payments:
                refund_amount = payment.amount

                # جلوگیری از واریز تکراری
                already_refunded = WalletTransaction.objects.filter(
                    wallet=wallet,
                    amount=refund_amount,
                    type='deposit',
                    description__icontains=f'بازگشت مبلغ {payment.get_payment_type_display()} سفارش لغو شده {instance.order_number}'
                ).exists()

                if not already_refunded:
                    wallet.balance += refund_amount
                    wallet.save()

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=refund_amount,
                        type='deposit',
                        description=f'بازگشت مبلغ {payment.get_payment_type_display()} سفارش لغو شده {instance.order_number}'
                    )
                    logger.info(f"💰 مبلغ {refund_amount} ریال از طریق {payment.get_payment_type_display()} به کیف پول بازگردانده شد.")


        # 4. حذف پاداش از کیف پول (در صورت وجود)
        if instance.reward_applied:
            wallet = instance.user.wallet
            
            # محاسبه مبلغ پرداخت شده از درگاه برای محاسبه پاداش
            gateway_payment = instance.payments.filter(
                payment_type='gateway', 
                status='completed'
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            reward = get_order_reward_amount(instance, gateway_payment)

            already_withdrawn = WalletTransaction.objects.filter(
                wallet=wallet,
                amount=reward,
                type='withdraw',
                description__icontains=f'حذف پاداش سفارش لغو شده {instance.order_number}'
            ).exists()

            if reward > 0 and wallet.balance >= reward and not already_withdrawn:
                wallet.balance -= reward
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=reward,  # مثبت بماند!
                    type='withdraw',
                    description=f'حذف پاداش سفارش لغو شده {instance.order_number}'
                )
                logger.info(f"❌ پاداش {reward} ریال از کیف پول کسر شد.")

            # برای اطمینان دوباره ست شود
            instance.reward_applied = False

@receiver(post_save, sender=PaymentMethod)
def handle_payment_method_save(sender, instance, created, **kwargs):
    """
    همگام‌سازی وضعیت پرداخت سفارش با روش‌های پرداخت
    """
    order = instance.order
    payments = order.payments.all()
    
    # محاسبه مجموع مبالغ پرداخت شده
    total_paid = sum(payment.amount for payment in payments if payment.status == 'completed')
    
    # اگر کل مبلغ پرداخت شده باشد
    if total_paid >= order.final_amount:
        order.payment_status = 'paid'
        order.unpaid_amount = 0

    # اگر پرداختی انجام نشده باشد
    elif total_paid == 0:
        order.payment_status = 'pending'
        order.unpaid_amount = order.final_amount

    # اگر بخشی پرداخت شده باشد
    else:
        order.payment_status = 'pending'  # تغییر: اگر بخشی پرداخت شده، هنوز pending است
        order.unpaid_amount = order.final_amount - total_paid

    order.save(update_fields=['unpaid_amount', 'payment_status'])



@receiver(pre_save, sender=PaymentMethod)
def validate_payment_method(sender, instance, **kwargs):
    """
    اعتبارسنجی روش پرداخت
    """
    if instance.status == 'completed':
        # بررسی اینکه مجموع مبالغ پرداخت شده از مبلغ کل سفارش بیشتر نباشد
        other_payments = instance.order.payments.exclude(id=instance.id).filter(status='completed')
        total_paid = sum(payment.amount for payment in other_payments) + instance.amount
        
        if total_paid > instance.order.final_amount:
            raise ValueError("مجموع مبالغ پرداخت شده نمی‌تواند از مبلغ کل سفارش بیشتر باشد.")