from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth import login
from django.conf import settings

from . models import CustomUser, CustomerProfile
from .forms import LoginForm, BeauticianForm, CustomerProfileForm, AddressForm, OTPForm, convert_persian_to_english, UpdateProfileForm
from .helper import send_otp_code, get_random_otp, check_otp_expiration, send_message
from .tasks import send_message_task


class LoginView(View):
    template_name = 'login.html'
    form_class = LoginForm

    def get(self, request):
        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            otp = get_random_otp()
            user, created = CustomUser.objects.update_or_create(phone_number=phone_number, defaults={'otp_code': otp,'is_active': False})
            send_message(phone_number, str(otp), template='levehaft-verification')  # ارسال مستقیم پیامک
            request.session['phone_number'] = phone_number
            return redirect('accounts:verify')
        return render(request, self.template_name, {'form': form})

def verify_otp_view(request):
    phone_number = request.session.get('phone_number')
    if not phone_number:
        return redirect('accounts:login')
    
    user = CustomUser.objects.select_related('profile').get(phone_number=phone_number)
    
    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_input = form.cleaned_data['otp']
            if not check_otp_expiration(phone_number):
                messages.error(request, 'کد OTP منقضی شده است!', 'danger')
                return redirect('accounts:verify')
            if str(user.otp_code) != otp_input:
                messages.error(request, 'کد OTP اشتباه است!', 'danger')
                return redirect('accounts:verify')
            
            user.is_active = True
            user.save(update_fields=['is_active'])
            login(request, user)
            del request.session['phone_number']
            messages.success(request, 'ثبت نام / ورود با موفقیت انجام پذیرفت')
            
            profile = user.profile
            if profile.first_name and profile.last_name:
                return redirect('pages:home')
            return redirect('accounts:complete_profile')
    else:
        form = OTPForm()
    
    return render(request, 'verify.html', {
        'phone_number': phone_number,
        'form': form
    })

@login_required
def complete_profile(request, user = None):
    user = CustomUser.objects.select_related('profile').get(id=request.user.id)
    profile = user.profile  # یک کوئری با استفاده از related_name
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save(update_fields=['first_name', 'last_name', 'email'])
            messages.success(request, 'اطلاعات کاربری شما با موفقیت ذخیره گردید')
            return redirect('pages:home')
    else:
        form = CustomerProfileForm(instance=profile, user=request.user)
    return render(request, 'complete_profile.html', {'form': form})

@login_required
def beautician_request(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = BeauticianForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            admin_phone = settings.ADMIN_PHONE
            message = f"{request.user.phone_number}"
            send_message(admin_phone, message, template='manager-notification')  # ارسال مستقیم پیامک
            messages.success(request, 'درخواست بیوتیشن شدن شما کاربر عزیز با موفقیت ارسال گردید')
            return redirect('pages:home')
    else:
        form = BeauticianForm(instance=profile)
    return render(request, 'beautician_request.html', {'form': form})

@login_required
def my_account_view(request):
    # یک کوئری بهینه برای دریافت اطلاعات کاربر و پروفایل
    user = CustomUser.objects.select_related(
        'profile'
    ).only(
        'first_name',
        'last_name',
        'phone_number',
        'email',
        'date_joined',
        'profile__is_beautician',
        'profile__first_name',
        'profile__last_name',
        'profile__birth_date',
        'profile__age',
        'profile__gender'
    ).get(id=request.user.id)

    # یک کوئری بهینه برای دریافت آدرس‌ها
    addresses = user.addresses.all().only(
        'province',
        'city',
        'address',
        'postal_code',
        'is_default'
    )

    # دریافت سفارش‌های کاربر
    orders = user.orders.select_related().prefetch_related(
        'items__product'
    ).order_by('-created_at')

    context = {
        'user': user,
        'profile': user.profile,
        'addresses': addresses,
        'orders': orders,
    }
    
    return render(request, 'my_account.html', context)

@login_required
def update_profile_view(request):
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            # به‌روزرسانی اطلاعات در مدل CustomUser
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            
            messages.success(request, 'اطلاعات شما با موفقیت به‌روزرسانی شد')
            return redirect('accounts:my_account')
    else:
        # پر کردن فرم با اطلاعات فعلی
        initial_data = {
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'email': user.email,
            'birth_date': profile.birth_date,
            'age': profile.age,
            'gender': profile.gender
        }
        form = UpdateProfileForm(instance=profile, initial=initial_data)
    
    return render(request, 'update_profile.html', {'form': form})

@login_required
def add_address_view(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'آدرس با موفقیت اضافه شد')
            return redirect('accounts:my_account')
    else:
        form = AddressForm()
    
    return render(request, 'add_address.html', {'form': form})


