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

            if reward > 0 and wallet.balance >= reward:
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





# @receiver(post_save, sender=Order)
# def handle_order_cancellation(sender, instance, created, **kwargs):
#     """
#     سیگنال برای بازگشت موجودی محصولات و بازپرداخت مبلغ به کیف پول پس از لغو سفارش
#     """
#     print("سیگنال لغو سفارش فراخوانی شد", instance.status)
#     if not created and instance.status == 'cancelled':
#         try:
#             old = sender.objects.get(pk=instance.pk)
#             print("سفارش قبلی یافت شد:", old.status)
#         except sender.DoesNotExist:
#             old = None
#             print("سفارش قبلی یافت نشد.")
        
#         # تغییر شرط: اگر وضعیت قبلی cancelled نبوده باشد
#         if old and old.status != 'cancelled':
#             print("سفارش لغو شده است و موجودی باید بازگردد")
#             # بازگشت موجودی محصولات
#             for item in instance.items.all():
#                 product = item.product
#                 product.stock += item.quantity
#                 product.save()
#                 print(f"[سیگنال لغو] موجودی محصول {product.name} به میزان {item.quantity} افزایش یافت.")
#             # بازپرداخت مبلغ به کیف پول
#             if instance.payment_status == 'paid':
#                 wallet = instance.user.wallet
#                 refund_amount = instance.final_amount
#                 wallet.balance += refund_amount
#                 wallet.save()
#                 WalletTransaction.objects.create(
#                     wallet=wallet,
#                     amount=refund_amount,
#                     type='deposit',
#                     description=f'بازپرداخت مبلغ سفارش لغو شده {instance.order_number}'
#                 )
#                 print(f"[سیگنال لغو] مبلغ {refund_amount} به کیف پول کاربر بازپرداخت شد.")
#             # اگر پاداش اعمال شده بود، آن را حذف کن
#             if instance.reward_applied:
#                 from wallet.services.wallet_services import get_order_reward_amount
#                 reward_amount = get_order_reward_amount(instance)
#                 if reward_amount > 0:
#                     wallet = instance.user.wallet
#                     wallet.balance -= reward_amount
#                     wallet.save()
#                     WalletTransaction.objects.create(
#                         wallet=wallet,
#                         amount=-reward_amount,
#                         type='withdraw',
#                         description=f'حذف پاداش سفارش لغو شده {instance.order_number}'
#                     )
#                     print(f"[سیگنال لغو] پاداش سفارش {instance.order_number} به مبلغ {reward_amount} از کیف پول کاربر کسر شد.")
#                 instance.reward_applied = False
#                 instance.save(update_fields=["reward_applied"]) 