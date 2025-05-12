from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    use_wallet = forms.BooleanField(required=False, label='استفاده از موجودی کیف پول برای پرداخت سفارش')
    class Meta:
        model = Order
        fields = [
            'receiver_name',
            'receiver_phone',
            'receiver_address',
            'receiver_city',
            'receiver_postal_code',
            'notes'
        ]
        widgets = {
            'receiver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام و نام خانوادگی گیرنده'}),
            'receiver_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره تماس گیرنده'}),
            'receiver_address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'آدرس کامل گیرنده', 'rows': 3}),
            'receiver_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهر گیرنده'}),
            'receiver_postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی گیرنده'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'توضیحات سفارش (اختیاری)', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # تنظیم نام و نام خانوادگی کاربر
            self.fields['receiver_name'].initial = f"{self.user.first_name} {self.user.last_name}"
            
            # اگر کاربر آدرس پیش‌فرض داشته باشد، آن را نمایش می‌دهیم
            default_address = self.user.addresses.filter(is_default=True).first()
            if default_address:
                self.fields['receiver_address'].initial = default_address.address
                self.fields['receiver_city'].initial = default_address.city
                self.fields['receiver_postal_code'].initial = default_address.postal_code
                self.fields['receiver_phone'].initial = self.user.phone_number

    def clean_receiver_phone(self):
        phone = self.cleaned_data['receiver_phone']
        if not phone.isdigit():
            raise forms.ValidationError('شماره تماس باید فقط شامل اعداد باشد')
        if len(phone) != 11:
            raise forms.ValidationError('شماره تماس باید 11 رقم باشد')
        return phone

    def clean_receiver_postal_code(self):
        postal_code = self.cleaned_data['receiver_postal_code']
        if not postal_code.isdigit():
            raise forms.ValidationError('کد پستی باید فقط شامل اعداد باشد')
        if len(postal_code) != 10:
            raise forms.ValidationError('کد پستی باید 10 رقم باشد')
        return postal_code 