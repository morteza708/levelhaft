from django.conf import settings
from accounts.helper import send_message
import logging

logger = logging.getLogger(__name__)

def send_reward_sms(user, amount, order_number):
    """ارسال پیامک پاداش خرید"""
    message = f"{amount:,}"
    send_message(
        user.phone_number,
        message,
        template='wallet-reward-customer'
    )
    logger.info(f"📤 پیامک پاداش خرید برای سفارش {order_number} ارسال شد")

def send_gift_wallet_sms(user, amount):
    """ارسال پیامک گیفت کیف پول"""
    message = f"{amount:,}"
    send_message(
        user.phone_number,
        message,
        template='wallet-gift-customer'
    )
    
def send_charge_sms(user, amount):
    """ارسال پیامک شارژ کیف پول"""
    message = f"{amount:,}"
    send_message(
        user.phone_number,
        message,
        template='wallet-charge-customer'
    )
    logger.info(f"📤 پیامک شارژ کیف پول برای کاربر {user.phone_number} ارسال شد")

def send_refund_sms(user, amount, order_number):
    """ارسال پیامک بازگشت وجه"""
    message = f"{amount:,}"
    send_message(
        user.phone_number,
        message,
        template='wallet-canceled-customer'
    )
    logger.info(f"📤 پیامک بازگشت وجه برای سفارش {order_number} ارسال شد")

def send_cancel_notification_to_admin(order):
    """ارسال پیامک اطلاع‌رسانی لغو سفارش به مدیر"""
    message = f"."
    send_message(
        settings.ADMIN_PHONE,
        message,
        template='canceled-notification-manager'
    )
    logger.info(f"📤 پیامک اطلاع‌رسانی لغو سفارش {order.order_number} به مدیر ارسال شد") 