from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Wallet
import math

class WalletRewardTests(TestCase):
    def setUp(self):
        # ایجاد کاربر عادی
        self.normal_user = get_user_model().objects.create_user(
            username='normal_user',
            email='normal@example.com',
            password='testpass123'
        )
        self.normal_user.profile.is_beautician = False
        self.normal_user.profile.save()
        
        # ایجاد کاربر بیوتیشن
        self.beautician = get_user_model().objects.create_user(
            username='beautician',
            email='beautician@example.com',
            password='testpass123'
        )
        self.beautician.profile.is_beautician = True
        self.beautician.profile.save()

    def test_reward_calculation(self):
        """تست محاسبه پاداش برای کاربران عادی و بیوتیشن"""
        from .services.wallet_services import get_order_reward_amount

        class MockOrder:
            def __init__(self, amount, user):
                self.total_amount = amount
                self.user = user

        # تست برای کاربر عادی (3%)
        test_cases_normal = [
            (100_000, 3_000),      # دقیقاً 3%
            (100_001, 3_001),      # گرد به بالا
            (1_000_000, 30_000),   # عدد بزرگتر
            (1_000_001, 30_001),   # گرد به بالا
        ]

        for amount, expected in test_cases_normal:
            order = MockOrder(amount, self.normal_user)
            reward = get_order_reward_amount(order)
            self.assertEqual(reward, expected, 
                f"برای مبلغ {amount:,} تومان، پاداش باید {expected:,} تومان باشد، اما {reward:,} تومان محاسبه شده است")

        # تست برای بیوتیشن (5%, 8%, 10%)
        test_cases_beautician = [
            (100_000_000, 5_000_000),      # 5% (کمتر از 200 میلیون)
            (199_999_999, 10_000_000),     # 5% (کمتر از 200 میلیون)
            (200_000_000, 16_000_000),     # 8% (دقیقاً 200 میلیون)
            (300_000_000, 24_000_000),     # 8% (بین 200 تا 400 میلیون)
            (399_999_999, 32_000_000),     # 8% (کمتر از 400 میلیون)
            (400_000_000, 40_000_000),     # 10% (دقیقاً 400 میلیون)
            (500_000_000, 50_000_000),     # 10% (بیشتر از 400 میلیون)
        ]

        for amount, expected in test_cases_beautician:
            order = MockOrder(amount, self.beautician)
            reward = get_order_reward_amount(order)
            self.assertEqual(reward, expected,
                f"برای مبلغ {amount:,} تومان، پاداش باید {expected:,} تومان باشد، اما {reward:,} تومان محاسبه شده است")
