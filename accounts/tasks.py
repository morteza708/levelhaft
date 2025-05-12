# accounts/tasks.py
from celery import shared_task
from .helper import send_message

@shared_task
def send_message_task(phone_number, message, template='levehaft-verification'):
    send_message(phone_number, message, template=template)