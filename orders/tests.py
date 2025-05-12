from django.test import TestCase
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order, OrderItem
from accounts.models import CustomerProfile

User = get_user_model()

class OrderCancelStockTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number='09125584599', password='testpass')
        CustomerProfile.objects.create(user=self.user, is_beautician=False)
        self.product = Product.objects.create(name='محصول تستی', barcode='123456', stock=10, price_level_2=10000)
        self.order = Order.objects.create(
            user=self.user,
            order_number='ORDTEST1',
            status='pending',
            payment_status='paid',
            total_amount=10000,
            final_amount=10000,
            receiver_name='گیرنده',
            receiver_phone='09125584599',
            receiver_address='آدرس',
            receiver_city='تهران',
            receiver_postal_code='1234567890',
        )
        OrderItem.objects.create(order=self.order, product=self.product, quantity=2, unit_price=10000, total_price=20000)

    def test_stock_increases_on_cancel(self):
        self.product.refresh_from_db()
        stock_before = self.product.stock
        # پرداخت سفارش (کاهش موجودی)
        self.order.payment_status = 'paid'
        self.order.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before - 2)
        # لغو سفارش (افزایش موجودی)
        self.order.status = 'cancelled'
        self.order.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_before, f"موجودی باید {stock_before} باشد اما {self.product.stock} است")
