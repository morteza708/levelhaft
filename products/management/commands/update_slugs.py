from django.core.management.base import BaseCommand
from products.models import Line, Product
from slugify import slugify

class Command(BaseCommand):
    help = 'Updates slugs for all Line and Product objects to English (transliterated) slugs.'

    def handle(self, *args, **options):
        # Update Line slugs
        lines = Line.objects.all()
        line_updated = 0
        
        for line in lines:
            old_slug = line.slug
            line.slug = slugify(line.name, separator='-')
            if old_slug != line.slug:
                line.save()
                line_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated slug for line "{line.name}" from "{old_slug}" to "{line.slug}"'
                    )
                )
        
        # Update Product slugs
        products = Product.objects.all()
        product_updated = 0
        
        for product in products:
            old_slug = product.slug
            product.slug = slugify(product.name, separator='-')
            if old_slug != product.slug:
                product.save()
                product_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated slug for product "{product.name}" from "{old_slug}" to "{product.slug}"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {line_updated} line slugs and {product_updated} product slugs'
            )
        ) 