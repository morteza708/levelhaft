class PaymentGateway:
    def request_payment(self, order, amount):
        """
        ارسال درخواست به درگاه و دریافت redirect_url.
        """
        raise NotImplementedError

    def verify_payment(self, request):
        """
        بررسی موفق بودن پرداخت بعد از بازگشت از درگاه.
        """
        raise NotImplementedError

# آماده برای توسعه آینده مثلاً ZarinpalGateway یا SamanGateway
