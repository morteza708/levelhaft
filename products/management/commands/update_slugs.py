from django.core.management.base import BaseCommand
from products.models import Line, Product
from products.utils import create_persian_slug

class Command(BaseCommand):
    help = 'Updates slugs for all Line and Product objects'

    def handle(self, *args, **options):
        # Update Line slugs
        lines = Line.objects.all()
        line_updated = 0
        
        for line in lines:
            old_slug = line.slug
            line.slug = create_persian_slug(line.name)
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
            product.slug = create_persian_slug(product.name)
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