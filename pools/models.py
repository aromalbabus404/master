from django.db import models


class HeroSection(models.Model):
    """Singleton row (pk=1) holding the storefront hero content."""
    eyebrow = models.CharField(max_length=200, default="Designed & Built in Kerala")
    heading = models.CharField(
        max_length=300, default="Pools shaped<br>around how you live",
        help_text="Use <br> for a line break, same as the original hero heading."
    )
    sub = models.TextField(
        default="From drone-surveyed site plans to the last pool light installed — "
                "custom swimming pools, renovations and premium accessories, delivered as one seamless build."
    )
    video_url = models.URLField(
        blank=True,
        default="https://cdn.coverr.co/videos/coverr-aerial-view-of-a-swimming-pool-2633/1080p.mp4",
    )
    poster_image = models.URLField(
        blank=True,
        default="https://images.unsplash.com/photo-1572331165267-854da2b10ccf?q=80&w=1600&auto=format&fit=crop",
    )
    stat1_value = models.CharField(max_length=20, default="240+")
    stat1_label = models.CharField(max_length=40, default="Pools Built")
    stat2_value = models.CharField(max_length=20, default="4.9★")
    stat2_label = models.CharField(max_length=40, default="Client Rating")
    stat3_value = models.CharField(max_length=20, default="12 Yrs")
    stat3_label = models.CharField(max_length=40, default="Experience")
    stat4_value = models.CharField(max_length=20, default="60+")
    stat4_label = models.CharField(max_length=40, default="Accessories")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton: never actually delete

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def stats(self):
        return [
            {"v": self.stat1_value, "l": self.stat1_label},
            {"v": self.stat2_value, "l": self.stat2_label},
            {"v": self.stat3_value, "l": self.stat3_label},
            {"v": self.stat4_value, "l": self.stat4_label},
        ]

    def __str__(self):
        return "Hero Section"


class SiteSettings(models.Model):
    """Singleton row (pk=1) holding site-wide settings."""
    admin_whatsapp = models.CharField(
        max_length=20, default="917356462150",
        help_text="Country code + number, digits only, no + or spaces. e.g. 917356462150"
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Site Settings"


CATEGORY_CHOICES = [
    ("pool", "Pool Designs"),
    ("pump", "Pumps & Filters"),
    ("light", "Lighting"),
    ("cover", "Covers & Ladders"),
    ("clean", "Cleaning"),
]


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="pool")
    badge = models.CharField(max_length=50, blank=True, null=True)
    price = models.PositiveIntegerField()
    mrp = models.PositiveIntegerField(blank=True, null=True, verbose_name="MRP (strikethrough price)")
    sizes = models.CharField(max_length=300, help_text="Comma separated, e.g. 20x10 ft, 25x12 ft")
    image_url = models.URLField(blank=True, null=True, help_text="Use this OR upload a file below.")
    image_file = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def image(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url or ""

    def size_list(self):
        return [s.strip() for s in self.sizes.split(",") if s.strip()]

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    image_url = models.URLField(blank=True, null=True)
    image_file = models.ImageField(upload_to="gallery/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def image(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url or ""

    def __str__(self):
        return f"Gallery image #{self.pk}"


STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]


class Review(models.Model):
    name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    text = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def avatar_url(self):
        from urllib.parse import quote
        return f"https://api.dicebear.com/7.x/initials/svg?seed={quote(self.name)}&backgroundColor=1FC8C2&textColor=ffffff"

    @property
    def stars_full(self):
        return range(self.rating)

    @property
    def stars_empty(self):
        return range(5 - self.rating)

    def __str__(self):
        return f"{self.name} ({self.rating}★) - {self.status}"


class ReviewMedia(models.Model):
    review = models.ForeignKey(Review, related_name="media", on_delete=models.CASCADE)
    file = models.FileField(upload_to="reviews/")
    is_video = models.BooleanField(default=False)

    def __str__(self):
        return f"Media for review #{self.review_id}"


class Order(models.Model):
    name = models.CharField(max_length=120)
    mobile = models.CharField(max_length=15)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=10)
    address = models.TextField()
    total = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} - {self.name} - ₹{self.total}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    size = models.CharField(max_length=100)
    qty = models.PositiveIntegerField()
    price = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.size}) x{self.qty}"
