from django import forms
from .models import Wallet
from products.utils import convert_to_english_digits

class WalletChargeForm(forms.Form):
    amount = forms.CharField(
        label='مبلغ شارژ (ریال)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مبلغ را به ریال وارد کنید',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        })
    )

    def clean_amount(self):
        raw = self.cleaned_data['amount']
        raw = convert_to_english_digits(str(raw)).replace(",", "").strip()
        try:
            amount = int(raw)
        except Exception:
            raise forms.ValidationError('مبلغ وارد شده معتبر نیست')
        if amount < 1000000:
            raise forms.ValidationError('حداقل مبلغ شارژ 1,000,000 ریال است')
        if amount > 150000000:
            raise forms.ValidationError('حداکثر مبلغ شارژ 150,000,000 ریال است')
        return amount 