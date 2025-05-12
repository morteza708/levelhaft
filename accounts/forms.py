# accounts/forms.py
from django import forms
from .models import CustomUser, CustomerProfile, Address
from django_jalali.forms import jDateField
import jdatetime
from datetime import datetime
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

def convert_persian_to_english(text):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    english_digits = '0123456789'
    translation_table = str.maketrans(persian_digits, english_digits)
    return text.translate(translation_table)

class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=4,
        label='کد تأیید',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'inputmode': 'numeric',
            'placeholder': 'کد تأیید را وارد کنید'
        })
    )

    def clean_otp(self):
        otp = self.cleaned_data['otp']
        return convert_persian_to_english(otp)

class LoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=11,
        label='شماره موبایل',
        widget=forms.TextInput(attrs={
            'placeholder': 'مثال: ۰۹۱۲۳۴۵۶۷۸۹',
            'class': 'form-control',
            'inputmode': 'numeric'
        }),
        help_text='لطفا شماره موبایل خود را با فرمت صحیح وارد کنید'
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        return convert_persian_to_english(phone_number)

class CustomerProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        max_length=11, 
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'inputmode': 'numeric'
        })
    )
    email = forms.EmailField(required=False)

    class Meta:
        model = CustomerProfile
        fields = ['first_name', 'last_name', 'birth_date', 'age', 'gender', 'email']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['birth_date'] = JalaliDateField(label='تاریخ تولد', widget=AdminJalaliDateWidget)
        if user:
            self.fields['phone_number'].initial = user.phone_number

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['province', 'city', 'address', 'postal_code', 'is_default']
        widgets = {
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'استان'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شهر'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'آدرس کامل'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پستی'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'province': 'استان',
            'city': 'شهر',
            'address': 'آدرس',
            'postal_code': 'کد پستی',
            'is_default': 'آدرس پیش‌فرض',
        }

    def clean_postal_code(self):
        postal_code = self.cleaned_data['postal_code']
        return convert_persian_to_english(postal_code)

class BeauticianForm(forms.ModelForm):
    class Meta:
        model = CustomerProfile
        fields = ['clinic_name', 'activity_city', 'activity_history', 'brand_used', 'instagram_url']

class UpdateProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='نام')
    last_name = forms.CharField(label='نام خانوادگی')
    email = forms.EmailField(label='ایمیل', required=False)
    age = forms.IntegerField(label='سن', required=False)
    gender = forms.ChoiceField(
        label='جنسیت',
        choices=[('', 'انتخاب کنید'), ('male', 'مرد'), ('female', 'زن')],
        required=False
    )

    class Meta:
        model = CustomerProfile
        fields = ['first_name', 'last_name', 'email', 'birth_date', 'age', 'gender']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_date'] = JalaliDateField(
            label='تاریخ تولد',
            widget=AdminJalaliDateWidget(
                attrs={
                    'class': 'form-control',
                    'data-jdp': True,
                }
            ),
            required=False
        )
