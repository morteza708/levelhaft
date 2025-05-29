from django.core.management.base import BaseCommand
from products.models import Line
from slugify import slugify

class Command(BaseCommand):
    help = 'Updates slugs for all Line objects to English (transliterated) slugs.'

    def handle(self, *args, **options):
        lines = Line.objects.all()
        updated = 0
        
        for line in lines:
            old_slug = line.slug
            line.slug = slugify(line.name, separator='-')
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