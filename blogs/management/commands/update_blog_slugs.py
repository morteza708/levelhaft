from django.core.management.base import BaseCommand
from blogs.models import BlogCategory, BlogPost
from blogs.utils import create_persian_slug

class Command(BaseCommand):
    help = 'Updates slugs for all BlogCategory and BlogPost objects'

    def handle(self, *args, **options):
        # Update BlogCategory slugs
        categories = BlogCategory.objects.all()
        category_updated = 0
        
        for category in categories:
            old_slug = category.slug
            category.slug = create_persian_slug(category.name)
            if old_slug != category.slug:
                category.save()
                category_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated slug for category "{category.name}" from "{old_slug}" to "{category.slug}"'
                    )
                )
        
        # Update BlogPost slugs
        posts = BlogPost.objects.all()
        post_updated = 0
        
        for post in posts:
            old_slug = post.slug
            post.slug = create_persian_slug(post.title)
            if old_slug != post.slug:
                post.save()
                post_updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated slug for post "{post.title}" from "{old_slug}" to "{post.slug}"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {category_updated} category slugs and {post_updated} post slugs'
            )
        ) 