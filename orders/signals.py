from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Order
from products.models import Product
from wallet.models import Wallet, WalletTransaction
from wallet.services.wallet_services import get_order_reward_amount
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

        # 1. بازگرداندن موجودی کالاها
        for item in instance.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
            logger.info(f"✅ موجودی '{product.name}' افزایش یافت: +{item.quantity}")

        # 2. بازگشت مبلغ سفارش به کیف پول
        if instance.payment_status == 'paid':
            wallet = instance.user.wallet
            refund_amount = instance.final_amount

            # جلوگیری از واریز تکراری
            already_refunded = WalletTransaction.objects.filter(
                wallet=wallet,
                amount=refund_amount,
                type='deposit',
                description__icontains=f'بازگشت مبلغ سفارش لغو شده {instance.order_number}'
            ).exists()

            if not already_refunded:
                wallet.balance += refund_amount
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    type='deposit',
                    description=f'بازگشت مبلغ سفارش لغو شده {instance.order_number}'
                )
                logger.info(f"💰 مبلغ {refund_amount} ریال به کیف پول بازگردانده شد.")

        # 3. حذف پاداش از کیف پول (در صورت وجود)
        if instance.reward_applied:
            wallet = instance.user.wallet
            reward = get_order_reward_amount(instance)

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