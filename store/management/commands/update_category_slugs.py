from django.core.management.base import BaseCommand
from store.models import Category
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Updates slugs for all categories'

    def handle(self, *args, **options):
        categories = Category.objects.all()
        for category in categories:
            old_slug = category.slug
            category.slug = slugify(category.name)
            if old_slug != category.slug:
                category.save()
                self.stdout.write(self.style.SUCCESS(f'Updated slug for {category.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Slug already correct for {category.name}')) 