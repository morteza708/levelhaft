# accounts/signals.py
from django.contrib.auth import user_logged_in
from django.dispatch import receiver
from .models import CustomUser, CustomerProfile

@receiver(user_logged_in, sender=CustomUser)
def create_customer_profile(sender, user, request, **kwargs):
    CustomerProfile.objects.get_or_create(user=user)