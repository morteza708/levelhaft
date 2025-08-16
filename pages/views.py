from django.shortcuts import render
from django.views.generic import TemplateView
from products.models import Product, ProductImage
from django.db.models import Prefetch
from .forms import ContactMessageForm
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Product, Brand, Line
from blogs.models import BlogPost
from workshop.models import Workshop
from django.utils import timezone
from datetime import datetime



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

def about_us_view(request):
    return render(request, 'about_us.html')

def contact_us_view(request):
    form = ContactMessageForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'پیام شما با موفقیت ارسال شد. کارشناسان ما در اسرع وقت پاسخ خواهند داد.')
            form = ContactMessageForm()  # فرم خالی شود
    return render(request, 'contact_us.html', {'form': form})

class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Product.objects.filter(is_featured=True)
    
    def lastmod(self, obj):
        return obj.created_at

# class BrandSitemap(Sitemap):  # حذف شده - URL برندها وجود ندارد
#     changefreq = 'monthly'
#     priority = 0.6
#     
#     def items(self):
#         return Brand.objects.filter(is_active=True)

class LineSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        return Line.objects.all()

class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return BlogPost.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.created_at

class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    
    def items(self):
        return [
            'home',
            'about_us',
            'contact_us',
            'product_list',
            'blog_list',
        ]
    
    def location(self, item):
        return reverse(item)

def sitemap_xml(request):
    """Generate sitemap.xml dynamically"""
    products = Product.objects.filter(is_featured=True)
    brands = Brand.objects.filter(is_active=True)
    lines = Line.objects.all()
    blogs = BlogPost.objects.filter(is_published=True)
    workshops = Workshop.objects.all()
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    
    <!-- Static Pages -->
    <url>
        <loc>https://levelhaft.com/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/about/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/contact/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/products/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/blogs/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/workshop/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/products/search/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/products/consult/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
    
    <url>
        <loc>https://levelhaft.com/products/accessories/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
    
    <!-- Featured Products -->
"""
    
    for product in products:
        xml_content += f"""    <url>
        <loc>https://levelhaft.com/products/product/{product.slug}/</loc>
        <lastmod>{product.created_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
"""
    

    
    xml_content += """    
    <!-- Lines -->
"""
    
    for line in lines:
        xml_content += f"""    <url>
        <loc>https://levelhaft.com/products/line/{line.slug}/</loc>
        <lastmod>{timezone.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.6</priority>
    </url>
"""
    
    xml_content += """    
    <!-- Blog Posts -->
"""
    
    for blog in blogs:
        xml_content += f"""    <url>
        <loc>https://levelhaft.com/blogs/{blog.slug}/</loc>
        <lastmod>{blog.created_at.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
"""
    
    xml_content += """    
    <!-- Workshops -->
"""
    
    for workshop in workshops:
        xml_content += f"""    <url>
        <loc>https://levelhaft.com/workshop/{workshop.id}/</loc>
        <lastmod>{workshop.date.strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
"""
    
    xml_content += """</urlset>"""
    
    return HttpResponse(xml_content, content_type='application/xml')