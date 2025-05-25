from django import forms
from .models import WorkshopRegistration
from django.core.exceptions import ValidationError
import re


class WorkshopRegistrationForm(forms.ModelForm):
    class Meta:
        model = WorkshopRegistration
        fields = ['first_name_en', 'last_name_en', 'clinic_name', 'city', 'address']
        widgets = {
            'first_name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام به انگلیسی',
                'dir': 'ltr'
            }),
            'last_name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام خانوادگی به انگلیسی',
                'dir': 'ltr'
            }),
            'clinic_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام کلینیک یا سالن زیبایی'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شهر محل فعالیت'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس دقیق محل فعالیت',
                'rows': 3
            })
        }
        labels = {
            'first_name_en': 'نام به انگلیسی',
            'last_name_en': 'نام خانوادگی به انگلیسی',
            'clinic_name': 'نام کلینیک',
            'city': 'شهر محل فعالیت',
            'address': 'آدرس محل فعالیت'
        }
        help_texts = {
            'first_name_en': 'لطفاً نام خود را به حروف انگلیسی وارد کنید',
            'last_name_en': 'لطفاً نام خانوادگی خود را به حروف انگلیسی وارد کنید',
            'clinic_name': 'نام کلینیک یا سالن زیبایی خود را وارد کنید',
            'city': 'نام شهر محل فعالیت خود را وارد کنید',
            'address': 'آدرس دقیق محل فعالیت خود را وارد کنید'
        }

    def clean_first_name_en(self):
        first_name = self.cleaned_data.get('first_name_en')
        if not re.match(r"^[a-zA-Z\s]*$", first_name):
            raise ValidationError('لطفاً فقط از حروف انگلیسی استفاده کنید')
        return first_name.title()

    def clean_last_name_en(self):
        last_name = self.cleaned_data.get('last_name_en')
        if not re.match(r"^[a-zA-Z\s]*$", last_name):
            raise ValidationError('لطفاً فقط از حروف انگلیسی استفاده کنید')
        return last_name.title()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.workshop = kwargs.pop('workshop', None)
        super().__init__(*args, **kwargs)
        
        # اضافه کردن کلاس‌های CSS
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': field.widget.attrs.get('class', '') + ' rounded-lg shadow-sm'
                })

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if self.workshop:
            instance.workshop = self.workshop
        if commit:
            instance.save()
        return instance
