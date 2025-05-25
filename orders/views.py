from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Order, OrderItem, OrderStatusHistory, PaymentMethod
from .forms import OrderForm
from cart.cart import Cart
from products.models import Product
from django.db import transaction
from wallet.models import Wallet, WalletTransaction
from wallet.services.wallet_services import apply_order_reward, deposit_to_wallet
from accounts.tasks import send_message_task
from django.conf import settings
from wallet.services.sms_service import send_refund_sms, send_cancel_notification_to_admin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

@login_required
def order_create(request):
    cart = Cart(request)
    if not cart:
        messages.error(request, 'سبد خرید شما خالی است')
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = OrderForm(request.POST, user=request.user)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            
            # محاسبه مبالغ
            total_amount = 0
            for item in cart:
                product = Product.objects.get(id=item['product_id'])
                quantity = item['quantity']
                price = item['price']
                total_amount += price * quantity

            # محاسبه هزینه ارسال (مثال ساده)
            shipping_cost = 0  # 50,000 ریال
            
            order.total_amount = total_amount
            order.shipping_cost = shipping_cost
            order.final_amount = total_amount + shipping_cost

            use_wallet = form.cleaned_data.get('use_wallet', False)
            unpaid_amount = order.final_amount
            wallet_used = 0
            with transaction.atomic():
                if use_wallet:
                    wallet = Wallet.objects.select_for_update().get(user=request.user)
                    if wallet.balance > 0:
                        if wallet.balance >= order.final_amount:
                            # کل مبلغ از کیف پول
                            wallet_used = order.final_amount
                            wallet.balance -= order.final_amount
                            order.payment_status = 'paid'
                            order.unpaid_amount = 0
                            
                            # ارسال پیامک به مشتری
                            message = f'....'
                            send_message_task.delay(
                                order.user.phone_number,
                                message,
                                template='order-confirmation'
                            )
                            
                            # ارسال پیامک به مدیر
                            send_message_task.delay(
                                settings.ADMIN_PHONE,
                                message,
                                template='manager-order-notification'
                            )
                        else:
                            # بخشی از مبلغ از کیف پول
                            wallet_used = wallet.balance
                            order.payment_status = 'pending'
                            order.unpaid_amount = order.final_amount - wallet.balance
                            wallet.balance = 0
                        wallet.save()
                    else:
                        order.payment_status = 'pending'
                        order.unpaid_amount = order.final_amount
                else:
                    order.payment_status = 'pending'
                    order.unpaid_amount = order.final_amount
                order.save()
                # کاهش موجودی محصولات فقط اگر پرداخت کامل شد
                if order.payment_status == 'paid':
                    for item in cart:
                        product = Product.objects.get(id=item['product_id'])
                        product.stock -= item['quantity']
                        product.save()
                product_ids = [item['product_id'] for item in cart]
                products = Product.objects.in_bulk(product_ids)
                for item in cart:
                    product = products.get(item['product_id'])
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        unit_price=item['price'],
                        total_price=item['total_price']
                    )

            # پاک کردن سبد خرید
            cart.clear()
            
            if order.payment_status == 'paid':
                messages.success(request, 'سفارش شما با موفقیت ثبت و پرداخت شد (از کیف پول)')
            elif wallet_used > 0:
                messages.info(request, f'بخشی از مبلغ سفارش از کیف پول شما کسر شد. مبلغ باقی‌مانده: {order.unpaid_amount:,} ریال')
            else:
                messages.info(request, 'سفارش شما ثبت شد. لطفاً مبلغ را پرداخت کنید.')

            # اعمال پاداش بلافاصله پس از پرداخت
            if order.payment_status == 'paid':
                apply_order_reward(order)
            return redirect('orders:order_detail', order_id=order.id)
    else:
        form = OrderForm(user=request.user)

    # نمایش موجودی کیف پول در قالب
    wallet_balance = 0
    if request.user.is_authenticated and hasattr(request.user, 'wallet'):
        wallet_balance = request.user.wallet.balance

    return render(request, 'orders/order_create.html', {
        'form': form,
        'cart': cart,
        'wallet_balance': wallet_balance
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {
        'order': order
    })

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user) \
    .prefetch_related('items') \
    .select_related('user') \
    .order_by('-created_at')
    return render(request, 'orders/order_list.html', {
        'orders': orders
    })

@login_required
@require_POST
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status not in ['pending']:
        return JsonResponse({
            'status': 'error',
            'message': 'این سفارش قابل لغو نیست'
        })
    
    order.status = 'cancelled'
    order.save()
    
    # ثبت تاریخچه تغییر وضعیت
    OrderStatusHistory.objects.create(
        order=order,
        old_status='pending' if order.status == 'pending' else 'processing',
        new_status='cancelled',
        changed_by=request.user,
        notes='لغو سفارش توسط کاربر'
    )
    
    # فقط ارسال پیامک و اطلاع‌رسانی (واریز وجه در سیگنال انجام می‌شود)
    if order.payment_status == 'paid':
        send_refund_sms(request.user, order.final_amount, order.order_number)
    
    send_cancel_notification_to_admin(order)
    
    return JsonResponse({
        'status': 'success',
        'message': 'سفارش با موفقیت لغو شد'
    }) 