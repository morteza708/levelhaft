from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from accounts.tasks import send_message_task
from .models import WorkshopRegistration, WorkshopRegistrationHistory


@receiver(post_save, sender=WorkshopRegistration)
def notify_new_registration(sender, instance, created, **kwargs):
    """
    ارسال اعلان به مدیر سایت برای ثبت‌نام جدید
    """
    if created:
        # ارسال پیامک به مدیر
        admin_message = f"ثبت نام جدید در ورکشاپ {instance.workshop.title}\nنام: {instance.user.get_full_name()}"
        # در اینجا می‌توانید شماره مدیر را از تنظیمات یا متغیرهای محیطی بخوانید
        # send_message_task.delay(ADMIN_PHONE, admin_message, template='workshop-admin-notification')


@receiver(pre_save, sender=WorkshopRegistration)
def handle_status_change(sender, instance, **kwargs):
    """
    مدیریت تغییر وضعیت ثبت‌نام و ارسال پیامک
    """
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            if instance.status == 'approved':
                # ارسال پیامک تایید به کاربر
                message = f"{instance.barcode}"
                send_message_task.delay(
                    instance.user.phone_number,
                    message,
                    template='workshop-verification'
                )
            elif instance.status == 'rejected':
                # ارسال پیامک رد درخواست به کاربر
                message = f"کاربر گرامی، متاسفانه ثبت نام شما در ورکشاپ {instance.workshop.title} تایید نشد."
                send_message_task.delay(
                    instance.user.phone_number,
                    message,
                    template='workshop-rejection'
                )
    except sender.DoesNotExist:
        pass  # این مورد برای ثبت‌نام‌های جدید است


@receiver(pre_save, sender=WorkshopRegistration)
def save_status_history(sender, instance, **kwargs):
    """
    ذخیره تاریخچه تغییرات وضعیت
    """
    try:
        old_instance = sender.objects.get(pk=instance.pk)
        if old_instance.status != instance.status:
            WorkshopRegistrationHistory.objects.create(
                registration=instance,
                old_status=old_instance.status,
                new_status=instance.status,
            )
    except sender.DoesNotExist:
        pass 