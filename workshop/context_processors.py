from .models import WorkshopBrand
from django.core.cache import cache


def workshop_brands_menu(request):
    """
    Context processor برای نمایش برندهای ورکشاپ در منو
    با استفاده از کش برای بهینه‌سازی
    """
    # سعی می‌کنیم برندها را از کش بخوانیم
    brands = cache.get('workshop_brands')
    
    # اگر در کش نبود، از دیتابیس می‌خوانیم
    if brands is None:
        brands = WorkshopBrand.objects.all().only('id', 'name', 'image')
        # ذخیره در کش برای 1 ساعت
        cache.set('workshop_brands', brands, 3600)
    
    return {'workshop_brands': brands} 