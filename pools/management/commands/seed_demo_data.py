from django.core.management.base import BaseCommand
from pools.models import Product, GalleryImage, HeroSection, SiteSettings


class Command(BaseCommand):
    help = "Seeds the database with the original demo products, gallery, hero text and settings."

    def handle(self, *args, **kwargs):
        HeroSection.load()   # creates default row if missing
        SiteSettings.load()  # creates default row if missing

        if not Product.objects.exists():
            Product.objects.create(
                name="Infinity Edge Pool Design", category="pool",
                image_url="https://images.unsplash.com/photo-1572331165267-854da2b10ccf?q=80&w=600&auto=format&fit=crop",
                price=185000, mrp=210000, badge="Bestseller",
                sizes="20x10 ft, 25x12 ft, 30x15 ft",
            )
            Product.objects.create(
                name="Plunge Pool Design", category="pool",
                image_url="https://images.unsplash.com/photo-1601436423145-3914d4459aff?q=80&w=600&auto=format&fit=crop",
                price=95000, sizes="10x8 ft, 12x10 ft",
            )
            Product.objects.create(
                name="Underwater LED Light", category="light",
                image_url="https://images.unsplash.com/photo-1602002418082-a4443e081dd1?q=80&w=600&auto=format&fit=crop",
                price=3499, mrp=4200, badge="New",
                sizes="RGB, Warm White, Cool White",
            )
            self.stdout.write(self.style.SUCCESS("Seeded 3 demo products."))

        if not GalleryImage.objects.exists():
            for url in [
                "https://images.unsplash.com/photo-1601436423145-3914d4459aff?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1564540583246-934409427776?q=80&w=800&auto=format&fit=crop",
                "https://images.unsplash.com/photo-1572331165267-854da2b10ccf?q=80&w=800&auto=format&fit=crop",
            ]:
                GalleryImage.objects.create(image_url=url)
            self.stdout.write(self.style.SUCCESS("Seeded 3 demo gallery images."))

        self.stdout.write(self.style.SUCCESS("Done."))
