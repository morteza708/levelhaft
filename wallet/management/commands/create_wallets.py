from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wallet.models import Wallet

class Command(BaseCommand):
    help = 'Creates wallets for users who don\'t have one'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users_without_wallet = User.objects.filter(wallet__isnull=True)
        
        for user in users_without_wallet:
            Wallet.objects.create(user=user)
            self.stdout.write(f'Created wallet for user {user.phone_number}') 