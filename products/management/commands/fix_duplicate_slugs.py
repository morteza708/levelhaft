from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product, Line
from slugify import slugify


class Command(BaseCommand):
    help = 'اصلاح اسلاگ‌های تکراری در محصولات و لاین‌ها'

    def handle(self, *args, **options):
        self.stdout.write('شروع اصلاح اسلاگ‌های تکراری...')
        
        # اصلاح اسلاگ‌های محصولات
        self.fix_product_slugs()
        
        # اصلاح اسلاگ‌های لاین‌ها
        self.fix_line_slugs()
        
        self.stdout.write(self.style.SUCCESS('اصلاح اسلاگ‌های تکراری با موفقیت انجام شد!'))

    def fix_product_slugs(self):
        """اصلاح اسلاگ‌های تکراری محصولات"""
        self.stdout.write('اصلاح اسلاگ‌های محصولات...')
        
        # پیدا کردن محصولاتی که اسلاگ ندارند
        products_without_slug = Product.objects.filter(slug='')
        for product in products_without_slug:
            self.generate_unique_slug(product, Product)
        
        # پیدا کردن محصولاتی با اسلاگ‌های تکراری
        seen_slugs = set()
        products = Product.objects.all().order_by('id')
        
        for product in products:
            if product.slug in seen_slugs:
                self.generate_unique_slug(product, Product)
            seen_slugs.add(product.slug)

    def fix_line_slugs(self):
        """اصلاح اسلاگ‌های تکراری لاین‌ها"""
        self.stdout.write('اصلاح اسلاگ‌های لاین‌ها...')
        
        # پیدا کردن لاین‌هایی که اسلاگ ندارند
        lines_without_slug = Line.objects.filter(slug='')
        for line in lines_without_slug:
            self.generate_unique_slug(line, Line)
        
        # پیدا کردن لاین‌هایی با اسلاگ‌های تکراری
        seen_slugs = set()
        lines = Line.objects.all().order_by('id')
        
        for line in lines:
            if line.slug in seen_slugs:
                self.generate_unique_slug(line, Line)
            seen_slugs.add(line.slug)

    def generate_unique_slug(self, obj, model_class):
        """تولید اسلاگ یکتا برای آبجکت"""
        base_slug = slugify(obj.name, separator='-')
        slug = base_slug
        counter = 1
        
        # بررسی یکتا بودن اسلاگ
        while model_class.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        obj.slug = slug
        obj.save(update_fields=['slug'])
        self.stdout.write(f'اسلاگ جدید برای {obj.name}: {slug}') 