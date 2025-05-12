from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Product, ProductImage
from django.db.models import Prefetch



def home_page_view(request):
    # دریافت محصولات ویژه با تصاویر و اطلاعات مرتبط
    featured_products = Product.objects.filter(
        is_featured=True
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.only('image', 'product_id')
        )
    ).select_related(
        'brand'
    ).only(
        'name',
        'slug',
        'price_level_1',
        'price_level_2',
        'brand__name'
    )

    # دریافت محصولات نمایش در صفحه اصلی با تصاویر و اطلاعات مرتبط
    home_products = Product.objects.filter(
        show_on_home=True
    ).prefetch_related(
        Prefetch(
            'images',
            queryset=ProductImage.objects.only('image', 'product_id')
        )
    ).select_related(
        'brand',
        'line',
        'usage_type',
        'model',
        'volume_unit'
    ).only(
        'name',
        'slug',
        'price_level_1',
        'price_level_2',
        'short_description',
        'brand__name',
        'line__name',
        'usage_type__name',
        'model__name',
        'volume_value',
        'volume_unit__name'
    )

    # فیلتر کردن محصولات هر برند به جز اکسسوری
    belter_products = home_products.filter(brand__name='دکتر بلتر').exclude(line__name='اکسسوری')
    racuten_products = home_products.filter(brand__name='راکوتن').exclude(line__name='اکسسوری')
    rimpler_products = home_products.filter(brand__name='دکتر ریمپلر').exclude(line__name='اکسسوری')
    isabelle_products = home_products.filter(brand__name='ایزابل لنکری').exclude(line__name='اکسسوری')
    ds_line_products = home_products.filter(brand__name='DS V-LINE').exclude(line__name='اکسسوری')
    cace_products = home_products.filter(brand__name='کیسی').exclude(line__name='اکسسوری')
    accessories_products = home_products.filter(line__name='اکسسوری')
    
    context = {
        'featured_products': featured_products,
        'home_products': home_products,
        'belter_products': belter_products,
        'racuten_products': racuten_products,
        'rimpler_products': rimpler_products,
        'isabelle_products': isabelle_products,
        'ds_line_products': ds_line_products,
        'cace_products': cace_products,
        'accessories_products': accessories_products
    }
    
    return render(request, 'home.html', context)

class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'صفحه اصلی'
        
        # دریافت محصولات ویژه با تصاویر و اطلاعات مرتبط
        featured_products = Product.objects.filter(
            is_featured=True
        ).prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.only('image', 'product_id')
            )
        ).select_related(
            'brand'
        ).only(
            'name',
            'slug',
            'price_level_1',
            'price_level_2',
            'brand__name'
        )

        # دریافت محصولات نمایش در صفحه اصلی با تصاویر و اطلاعات مرتبط
        home_products = Product.objects.filter(
            show_on_home=True
        ).prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.only('image', 'product_id')
            )
        ).select_related(
            'brand',
            'line',
            'usage_type',
            'model',
            'volume_unit'
        ).only(
            'name',
            'slug',
            'price_level_1',
            'price_level_2',
            'short_description',
            'brand__name',
            'line__name',
            'usage_type__name',
            'model__name',
            'volume_value',
            'volume_unit__name'
        )

        # فیلتر کردن محصولات هر برند به جز اکسسوری
        context['featured_products'] = featured_products
        context['home_products'] = home_products
        context['belter_products'] = home_products.filter(brand__name='دکتر بلتر').exclude(line__name='اکسسوری')
        context['racuten_products'] = home_products.filter(brand__name='راکوتن').exclude(line__name='اکسسوری')
        context['rimpler_products'] = home_products.filter(brand__name='دکتر ریمپلر').exclude(line__name='اکسسوری')
        context['isabelle_products'] = home_products.filter(brand__name='ایزابل لنکری').exclude(line__name='اکسسوری')
        context['ds_line_products'] = home_products.filter(brand__name='DS V-LINE').exclude(line__name='اکسسوری')
        context['cace_products'] = home_products.filter(brand__name='کیسی').exclude(line__name='اکسسوری')
        context['accessories_products'] = home_products.filter(line__name='اکسسوری')
        
        return context