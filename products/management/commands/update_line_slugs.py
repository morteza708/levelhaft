from django.core.management.base import BaseCommand
from products.models import Line
from products.utils import create_persian_slug

class Command(BaseCommand):
    help = 'Updates slugs for all Line objects'

    def handle(self, *args, **options):
        lines = Line.objects.all()
        updated = 0
        
        for line in lines:
            old_slug = line.slug
            line.slug = create_persian_slug(line.name)
            if old_slug != line.slug:
                line.save()
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated slug for line "{line.name}" from "{old_slug}" to "{line.slug}"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated} line slugs'
            )
        ) 