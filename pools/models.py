from django.db import models
from cloudinary.models import CloudinaryField
import json


class HeroSection(models.Model):
    """Singleton row (pk=1) holding the storefront hero TEXT content only.
    The background video/poster image are now plain static files bundled
    with the project (see static/pools/hero.mp4 and static/pools/hero-poster.jpg)
    — no upload, no Cloudinary, no admin-dashboard management needed for them.
    To change the video/image, just replace those files in your static
    folder and run collectstatic / redeploy."""

    eyebrow = models.CharField(
        max_length=200,
        default="Designed & Built in Kerala"
    )

    heading = models.CharField(
        max_length=300,
        default="Pools shaped<br>around how you live",
        help_text="Use <br> for a line break."
    )

    sub = models.TextField(
        default="From drone-surveyed site plans to the last pool light installed — "
                "custom swimming pools, renovations and premium accessories, delivered as one seamless build."
    )

    stat1_value = models.CharField(max_length=20, default="240+")
    stat1_label = models.CharField(max_length=40, default="Pools Built")

    stat2_value = models.CharField(max_length=20, default="4.9★")
    stat2_label = models.CharField(max_length=40, default="Client Rating")

    stat3_value = models.CharField(max_length=20, default="12 Yrs")
    stat3_label = models.CharField(max_length=40, default="Experience")

    stat4_value = models.CharField(max_length=20, default="60+")
    stat4_label = models.CharField(max_length=40, default="Accessories")

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

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

VARIANT_TYPE_CHOICES = [
    ("inches", "Inches"),
    ("sizes", "Sizes"),
]


def _safe_json_list(value):
    """
    Defensively normalizes any stored value into a clean Python list of
    non-empty strings — no matter how it actually got into the DB:
      - a real list (the normal case, e.g. ["Blue", "Red"]) -> cleaned as-is
      - a JSON string like '["Blue", "Red"]'                -> parsed
      - a plain comma string like "Blue, Red"                -> split
      - None / "" / [] / garbage                             -> []
    """
    if not value:
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except (ValueError, TypeError):
            pass
        return [c.strip() for c in s.split(",") if c.strip()]

    return []


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="pool")
    badge = models.CharField(max_length=50, blank=True, null=True)
    price = models.PositiveIntegerField()
    mrp = models.PositiveIntegerField(blank=True, null=True, verbose_name="MRP (strikethrough price)")
    sizes = models.CharField(max_length=300, help_text="Comma separated, e.g. 20x10 ft, 25x12 ft")

    size_prices = models.JSONField(default=dict, blank=True)

    variant_type = models.CharField(
        max_length=10, choices=VARIANT_TYPE_CHOICES, default="inches"
    )

    colors = models.JSONField(default=list, blank=True)

    image_url = models.URLField(blank=True, null=True, help_text="Use this OR upload a file below.")
    image_file = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def image(self):
        if self.image_file:
            return self.image_file.url
        return self.image_url or ""

    def size_list(self):
        return [s.strip() for s in self.sizes.split(",") if s.strip()]

    @property
    def sorted_sizes(self):
        if not self.size_prices:
            return []
        try:
            return sorted(self.size_prices.items(), key=lambda kv: float(kv[0]))
        except (ValueError, TypeError):
            return list(self.size_prices.items())

    @property
    def size_prices_json(self):
        return json.dumps(self.size_prices or {})

    @property
    def color_list(self):
        return _safe_json_list(self.colors)

    @property
    def colors_json(self):
        return json.dumps(self.color_list)

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    image_url = models.URLField(blank=True, null=True)

    image_file = CloudinaryField(
        "image",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image_file:
            self.image_url = self.image_file.build_url()
            super().save(update_fields=["image_url"])

    @property
    def image(self):
        if self.image_file:
            return self.image_file.build_url()
        return self.image_url or ""

    def __str__(self):
        return f"Gallery Image #{self.pk}"


class Client(models.Model):
    """A company / resort / hotel logo shown in the "Trusted By" section
    on the storefront. Fully manageable from the admin dashboard — add a
    name plus a logo (URL or upload), or delete one — and it updates
    everywhere immediately, just like Gallery images do."""

    name = models.CharField(max_length=200)

    image_url = models.URLField(blank=True, null=True)

    image_file = CloudinaryField(
        "image",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image_file:
            self.image_url = self.image_file.build_url()
            super().save(update_fields=["image_url"])

    @property
    def image(self):
        if self.image_file:
            return self.image_file.build_url()
        return self.image_url or ""

    def __str__(self):
        return self.name


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