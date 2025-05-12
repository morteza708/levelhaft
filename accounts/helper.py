import datetime
from http.client import HTTPException
from kavenegar import KavenegarAPI, APIException
from config.settings import Kavenegar_API
from random import randint
from .models import CustomUser
from django.utils import timezone


def send_otp_code(phone_number, otp_code):
    message = otp_code
    send_message(phone_number, str(message), template='levehaft-verification')

def send_message(phone_number, message, template='levehaft-verification'):
    try:
        api = KavenegarAPI(Kavenegar_API)
        params = {
            'receptor': f'{phone_number}',
            'template': template,
            'token': message,
            'type': 'sms',#sms vs call
        }
        response = api.verify_lookup(params)
        print(response)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)



def get_random_otp():
    return randint(1000, 9999)

def check_otp_expiration(phone_number):
    try:
        user = CustomUser.objects.get(phone_number=phone_number)
        now = datetime.datetime.now(tz=datetime.timezone.utc)  # استفاده از UTC برای هماهنگی
        otp_time = user.otp_code_created
        diff_time = now - otp_time
        print(f"Uptime: {diff_time}")
        return diff_time.seconds <= 300  # ساده‌سازی شرط
    except CustomUser.DoesNotExist:
        return False




def clean_expired_otp():
    threshold = timezone.now() - timezone.timedelta(seconds=120)
    CustomUser.objects.filter(otp_code_created__lt=threshold).update(otp_code=None, otp_code_created=None)






