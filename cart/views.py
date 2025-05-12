from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from products.models import Product
from .cart import Cart
from .forms import CartAddProductForm
from django.contrib import messages

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        try:
            cart.add(product=product,
                    quantity=cd['quantity'],
                    update_quantity=bool(cd['update']))
            messages.success(request, 'محصول با موفقیت به سبد خرید اضافه شد')
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('cart:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    # Create a list of cart items with their forms
    cart_items = []
    for item in cart:
        cart_items.append({
            'product': item,
            'quantity': item['quantity'],
            'update_quantity_form': CartAddProductForm(
                initial={'quantity': item['quantity'],
                        'update': True})
        })
    return render(request, 'cart/detail.html', {'cart_items': cart_items}) 
    