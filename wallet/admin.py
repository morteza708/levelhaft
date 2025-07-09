from django.contrib import admin
from .models import Wallet, WalletTransaction
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect, render
from django.contrib import messages
from .services.sms_service import send_gift_wallet_sms
from django.contrib.admin import SimpleListFilter
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe

class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('amount_display', 'type_display', 'description', 'created_at_jalali')
    can_delete = False
    show_change_link = True
    fields = ('amount_display', 'type_display', 'description', 'created_at_jalali')
    ordering = ('-created_at',)

    def amount_display(self, obj):
        amount = getattr(obj, 'amount', 0)
        if amount is None:
            return "-"
        return mark_safe(f"{amount:,} ریال")
    amount_display.short_description = 'مبلغ'

    def type_display(self, obj):
        return obj.get_type_display()
    type_display.short_description = 'نوع تراکنش'

    def created_at_jalali(self, obj):
        return obj.get_jalali_created_at()
    created_at_jalali.short_description = 'تاریخ (شمسی)'

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'balance_display', 'transaction_count', 'last_transaction', 'gift_wallet_link')
    search_fields = ('user__phone_number', 'user__email')
    list_filter = ('balance',)
    inlines = [WalletTransactionInline]
    readonly_fields = ('user_display', 'balance_display')

    def user_display(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.phone_number})"
    user_display.short_description = 'کاربر'

    def balance_display(self, obj):
        balance = getattr(obj, 'balance', 0)
        if balance is None:
            return "-"
        return f"{balance:,} ریال"
    balance_display.short_description = 'موجودی کیف پول'

    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'تعداد تراکنش‌ها'

    def last_transaction(self, obj):
        last = obj.transactions.order_by('-created_at').first()
        if last:
            amount = getattr(last, 'amount', 0)
            if amount is None:
                return f"{last.get_type_display()} - - ریال"
            return f"{last.get_type_display()} - {amount:,} ریال"
        return '-'
    last_transaction.short_description = 'آخرین تراکنش'

    def gift_wallet_link(self, obj):
        url = reverse('admin:wallet_wallet_gift_wallet', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">گیفت/شارژ کیف پول</a>',
            url
        )
    gift_wallet_link.short_description = 'گیفت کیف پول'
    gift_wallet_link.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/gift_wallet/',
                self.admin_site.admin_view(self.gift_wallet_view),
                name='wallet_wallet_gift_wallet',
            ),
        ]
        return custom_urls + urls

    def gift_wallet_view(self, request, object_id):
        wallet = Wallet.objects.get(pk=object_id)
        if request.method == 'POST':
            amount = int(request.POST.get('amount', 0))
            description = request.POST.get('description', 'گیفت ادمین')
            if amount <= 0:
                messages.error(request, 'مبلغ باید بیشتر از صفر باشد.')
            else:
                wallet.balance += amount
                wallet.save()
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    type='deposit',
                    description=description
                )
                send_gift_wallet_sms(wallet.user, amount)
                messages.success(request, f'کیف پول با موفقیت شارژ شد و پیامک ارسال گردید ({intcomma(amount)} ریال).')
                return redirect(f'/admin/wallet/wallet/{wallet.id}/change/')
        return render(request, 'admin/wallet/gift_wallet.html', {'wallet': wallet})

class PhoneNumberFilter(SimpleListFilter):
    title = 'شماره تماس کاربر'
    parameter_name = 'phone_number'

    def lookups(self, request, model_admin):
        return []

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(wallet__user__phone_number__icontains=value)
        return queryset

class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_display', 'user_display', 'phone_number', 'amount_display', 'type_display', 'description', 'created_at_jalali')
    list_filter = ('type', 'created_at', PhoneNumberFilter)
    search_fields = ('wallet__user__phone_number', 'wallet__user__email', 'description')
    readonly_fields = ('wallet_display', 'user_display', 'phone_number', 'amount_display', 'type_display', 'description', 'created_at_jalali')
    ordering = ('-created_at',)

    def wallet_display(self, obj):
        return f"کیف پول {obj.wallet.user.get_full_name() or obj.wallet.user.username}"
    wallet_display.short_description = 'کیف پول'

    def user_display(self, obj):
        return obj.wallet.user.get_full_name() or obj.wallet.user.username
    user_display.short_description = 'کاربر'

    def phone_number(self, obj):
        return obj.wallet.user.phone_number
    phone_number.short_description = 'شماره تماس'

    def amount_display(self, obj):
        amount = getattr(obj, 'amount', 0)
        if amount is None:
            return "-"
        return f"{amount:,} ریال"
    amount_display.short_description = 'مبلغ'

    def type_display(self, obj):
        return obj.get_type_display()
    type_display.short_description = 'نوع تراکنش'

    def created_at_jalali(self, obj):
        return obj.get_jalali_created_at()
    created_at_jalali.short_description = 'تاریخ (شمسی)'

admin.site.register(Wallet, WalletAdmin)
admin.site.register(WalletTransaction, WalletTransactionAdmin)
