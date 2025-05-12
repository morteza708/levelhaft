from django.conf import settings
from products.models import Product

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart
        self.request = request

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        
        # Check if requested quantity is available
        if quantity > product.stock:
            raise ValueError(f"تعداد درخواستی بیشتر از موجودی است. موجودی: {product.stock}")
            
        if product_id not in self.cart:
            # Check if user is authenticated and is a beautician
            if self.request.user.is_authenticated and hasattr(self.request.user, 'profile') and self.request.user.profile.is_beautician:
                price = str(product.price_level_1)
            else:
                price = str(product.price_level_2)
                
            self.cart[product_id] = {
                'quantity': 0,
                'price': price,
                'name': product.name,
                'image': product.images.first().image.url if product.images.exists() else None,
                'product_id': product.id,
                'stock': product.stock
            }
        
        if update_quantity:
            if quantity > product.stock:
                raise ValueError(f"تعداد درخواستی بیشتر از موجودی است. موجودی: {product.stock}")
            self.cart[product_id]['quantity'] = quantity
        else:
            new_quantity = self.cart[product_id]['quantity'] + quantity
            if new_quantity > product.stock:
                raise ValueError(f"تعداد درخواستی بیشتر از موجودی است. موجودی: {product.stock}")
            self.cart[product_id]['quantity'] = new_quantity

        self.save()

    def get_available_quantity(self, product):
        """Get available quantity for a product considering current cart items"""
        product_id = str(product.id)
        current_quantity = self.cart.get(product_id, {}).get('quantity', 0)
        return product.stock - current_quantity

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        for item in self.cart.values():
            item['price'] = int(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(int(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        self.session['cart'] = {}
        self.save()