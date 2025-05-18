from django import forms
from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'نام شما'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'ایمیل'}),
            'subject': forms.TextInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'موضوع پیام'}),
            'message': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 5, 'placeholder': 'متن پیام'}),
        } 