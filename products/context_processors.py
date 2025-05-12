from django.db.models import Prefetch
from .models import Brand, Line

def brands_menu(request):
    # استفاده از select_related و prefetch_related برای جلوگیری از N+1 query
    brands = Brand.objects.prefetch_related(
        Prefetch(
            'lines',
            queryset=Line.objects.only('id', 'name', 'slug', 'brand_id')
        )
    ).only('id', 'name').all()
    
    return {
        'brands_menu': brands
    } 