from django import forms
from .models import Product, Comment
from .utils import convert_to_english_digits

class ProductForm(forms.ModelForm):
    price_level_1 = forms.CharField(
        widget=forms.TextInput(attrs={'dir': 'ltr'}), 
        required=False,
        label="قیمت بیوتیشن"
    )
    price_level_2 = forms.CharField(
        widget=forms.TextInput(attrs={'dir': 'ltr'}), 
        required=False,
        label="قیمت عادی"
    )
    volume_value = forms.CharField(
        widget=forms.TextInput(attrs={'dir': 'ltr'}), 
        required=False,
        label="مقدار حجم"
    )

    class Meta:
        model = Product
        fields = '__all__'

    def clean_price_level_1(self):
        raw = self.cleaned_data.get("price_level_1")
        if raw:
            raw = convert_to_english_digits(raw).replace(",", "").strip()
            try:
                return int(raw)
            except ValueError:
                raise forms.ValidationError("عدد وارد شده معتبر نیست.")
        return None

    def clean_price_level_2(self):
        raw = self.cleaned_data.get("price_level_2")
        if raw:
            raw = convert_to_english_digits(raw).replace(",", "").strip()
            try:
                return int(raw)
            except ValueError:
                raise forms.ValidationError("عدد وارد شده معتبر نیست.")
        return None

    def clean_volume_value(self):
        raw = self.cleaned_data.get("volume_value")
        if raw:
            raw = convert_to_english_digits(raw).replace(",", "").strip()
            try:
                return int(raw)
            except ValueError:
                raise forms.ValidationError("عدد وارد شده معتبر نیست.")
        return None

class ProductAdminForm(ProductForm):
    class Meta(ProductForm.Meta):
        model = Product
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        # اگر هر دو قیمت خالی باشند، خطا نمی‌دهد
        price_level_1 = cleaned_data.get('price_level_1')
        price_level_2 = cleaned_data.get('price_level_2')
        volume_value = cleaned_data.get('volume_value')
        
        # تبدیل اعداد فارسی به انگلیسی
        if price_level_1:
            cleaned_data['price_level_1'] = convert_to_english_digits(str(price_level_1))
        if price_level_2:
            cleaned_data['price_level_2'] = convert_to_english_digits(str(price_level_2))
        if volume_value:
            cleaned_data['volume_value'] = convert_to_english_digits(str(volume_value))
            
        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'rating']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'نظر خود را بنویسید...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'style': 'display: none;'
            })
        }
        labels = {
            'text': 'متن نظر',
            'rating': 'امتیاز'
        }