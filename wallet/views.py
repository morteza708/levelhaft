from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet
from .forms import WalletChargeForm
from .services.wallet_services import deposit_to_wallet
from .services.sms_service import send_charge_sms

# Create your views here.

@login_required
def wallet_detail(request):
    wallet = request.user.wallet
    transactions = wallet.transactions.all().order_by('-created_at')[:10]
    return render(request, 'wallet/wallet_detail.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required
def charge_wallet(request):
    if request.method == 'POST':
        form = WalletChargeForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            wallet = request.user.wallet
            deposit_to_wallet(wallet, amount, description="شارژ کیف پول")
            # ارسال پیامک شارژ
            send_charge_sms(request.user, amount)
            messages.success(request, f'مبلغ {amount:,} ریال با موفقیت به کیف پول شما اضافه شد')
            return redirect('wallet:detail')
    else:
        form = WalletChargeForm()
    
    return render(request, 'wallet/charge_wallet.html', {'form': form})
