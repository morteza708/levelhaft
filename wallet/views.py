from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, WalletTransaction
from .forms import WalletChargeForm
from .services.wallet_services import deposit_to_wallet
from .services.sms_service import send_charge_sms
from gateways.pasargad import request_payment_url, get_token, BASE_URL
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import requests

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
            
            # ایجاد تراکنش با وضعیت در انتظار
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                type='deposit',
                description="شارژ کیف پول"
            )
            
            # ساخت callback url
            callback_url = request.build_absolute_uri(
                reverse('wallet:charge_callback')
            )
            
            try:
                # دریافت لینک پرداخت از پاسارگاد
                pay_url = request_payment_url(
                    invoice_id=transaction.id,
                    amount=amount,
                    callback_url=callback_url,
                    description="شارژ کیف پول",
                    phone_number=request.user.phone_number
                )
                return redirect(pay_url)
            except Exception as e:
                messages.error(request, f"خطا در اتصال به درگاه: {e}")
                return redirect('wallet:detail')
    else:
        form = WalletChargeForm()
    
    return render(request, 'wallet/charge_wallet.html', {'form': form})

def verify_wallet_payment(invoice, amount):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "invoice": str(invoice),
        "amount": int(amount),
    }
    response = requests.post(f"{BASE_URL}/verify", json=payload, headers=headers)
    data = response.json()
    return data

@csrf_exempt
def charge_callback(request):
    # دریافت داده‌ها از GET یا POST
    data = request.POST or request.GET
    invoice_id = data.get("invoiceId") or data.get("invoice")
    
    try:
        transaction = WalletTransaction.objects.get(id=invoice_id)
    except WalletTransaction.DoesNotExist:
        messages.error(request, "تراکنش یافت نشد.")
        return redirect('wallet:detail')

    # verify پرداخت از سرور پاسارگاد
    verify_result = verify_wallet_payment(invoice=transaction.id, amount=transaction.amount)
    
    if verify_result.get("resultCode") == 0:
        # پرداخت موفق
        deposit_to_wallet(transaction.wallet, transaction.amount, description="شارژ موفق کیف پول")
        send_charge_sms(transaction.wallet.user, transaction.amount)
        messages.success(request, f'مبلغ {transaction.amount:,} ریال با موفقیت به کیف پول شما اضافه شد')
    else:
        messages.error(request, "پرداخت ناموفق بود.")
    
    return redirect('wallet:detail')
