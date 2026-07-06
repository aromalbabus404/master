from django.db import models
from cloudinary.models import CloudinaryField
import cloudinary.uploader
import json


class HeroSection(models.Model):
    """Singleton row (pk=1) holding the storefront hero content."""

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

    # URL fields (optional)
    video_url = models.URLField(
        blank=True,
        default="https://cdn.coverr.co/videos/coverr-aerial-view-of-a-swimming-pool-2633/1080p.mp4",
    )

    poster_image = models.URLField(
        blank=True,
        default="https://images.unsplash.com/photo-1572331165267-854da2b10ccf?q=80&w=1600&auto=format&fit=crop",
    )

    # Cloudinary Video
    video_file = CloudinaryField(
        resource_type="video",
        blank=True,
        null=True,
    )

    # Cloudinary Image
    poster_image_file = CloudinaryField(
        "image",
        blank=True,
        null=True,
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

        # ------------------------------------------------------------
        # STEP 1 — capture the OLD Cloudinary public_id(s) from the
        # database BEFORE saving, so we know what to clean up
        # afterwards. This is safe to read now because `old` comes
        # straight from the DB, so its video_file/poster_image_file are
        # already real Cloudinary objects (not raw upload data).
        # ------------------------------------------------------------
        old_video_public_id = None
        old_poster_public_id = None

        try:
            old = HeroSection.objects.get(pk=self.pk)
            old_video_public_id = old.video_file.public_id if old.video_file else None
            old_poster_public_id = old.poster_image_file.public_id if old.poster_image_file else None
        except HeroSection.DoesNotExist:
            # First-ever save (no existing row yet) — nothing old to delete.
            pass

        # ------------------------------------------------------------
        # STEP 2 — save now. IMPORTANT: if a new video/image was just
        # submitted, `self.video_file` / `self.poster_image_file` are
        # STILL the raw uploaded file objects at this point (e.g. an
        # InMemoryUploadedFile) — NOT yet Cloudinary objects. They only
        # get converted (and gain a `.public_id`) during this
        # super().save() call, inside CloudinaryField's own pre_save().
        # Reading `.public_id` any earlier than this raises
        # AttributeError — which is exactly the bug this fixes.
        # ------------------------------------------------------------
        super().save(*args, **kwargs)

        update_fields = []

        if self.video_file:
            # Force delivery as .mp4 regardless of the source format the
            # admin uploaded (iPhones commonly upload .mov, some browsers/
            # cameras send .mkv/.avi/.3gp). Without forcing the format,
            # Cloudinary keeps the ORIGINAL container in the delivery URL —
            # meanwhile the storefront template hard-codes
            # <source type="video/mp4">. That mismatch is exactly why an
            # uploaded video can "successfully upload" but never actually
            # play: the browser is told it's MP4 while the URL serves a
            # .mov (or other) file.
            new_video_url = self.video_file.build_url(
                resource_type="video",
                format="mp4",
            )
            if new_video_url != self.video_url:
                self.video_url = new_video_url
                update_fields.append("video_url")

        if self.poster_image_file:
            new_poster_url = self.poster_image_file.build_url()
            if new_poster_url != self.poster_image:
                self.poster_image = new_poster_url
                update_fields.append("poster_image")

        # Only issue a second UPDATE if something actually changed —
        # avoids an unnecessary extra query on every plain text-field save.
        if update_fields:
            super().save(update_fields=update_fields)

        # ------------------------------------------------------------
        # STEP 3 — NOW it's safe to read .public_id on the new files:
        # super().save() has already run, so self.video_file and
        # self.poster_image_file are guaranteed to be real Cloudinary
        # objects (or None, if cleared). Compare against the OLD
        # public_ids captured in Step 1, and delete whichever old
        # asset(s) were actually replaced OR removed — so Cloudinary
        # storage doesn't quietly fill up with orphaned files every
        # time an admin uploads a new hero video/image, or explicitly
        # removes one via hero_remove_file.
        # ------------------------------------------------------------
        new_video_public_id = self.video_file.public_id if self.video_file else None
        new_poster_public_id = self.poster_image_file.public_id if self.poster_image_file else None

        if old_video_public_id and old_video_public_id != new_video_public_id:
            try:
                cloudinary.uploader.destroy(
                    old_video_public_id,
                    resource_type="video",
                )
            except Exception:
                # Never let a Cloudinary cleanup failure break the save —
                # worst case an old file lingers, which is recoverable
                # manually; a raised exception here would be worse (it
                # would look like the whole hero-section save failed).
                pass

        if old_poster_public_id and old_poster_public_id != new_poster_public_id:
            try:
                cloudinary.uploader.destroy(
                    old_poster_public_id,
                    resource_type="image",
                )
            except Exception:
                pass

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

    @property
    def poster_url(self):
        """Alias so templates can use hero.poster_url regardless of
        whether the poster came from an uploaded file or a plain URL —
        `poster_image` already holds the correct delivery URL either way
        (save() above rewrites it to the Cloudinary URL on upload).
        Previously templates referenced hero.poster_url, which did not
        exist on this model — Django templates fail silently on missing
        attributes, so the poster fallback never actually rendered."""
        return self.poster_image or ""

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
    This protects color_list/colors_json from ever throwing or silently
    returning nothing, even if a row was edited manually via /admin/,
    a fixture, or an older version of this model.
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

    # Per-size pricing, e.g. {"6": 300, "8": 500} — size (inches) -> price (₹).
    # `price` above is kept in sync automatically (set to the lowest size price)
    # so anything still reading `product.price` continues to work.
    size_prices = models.JSONField(default=dict, blank=True)

    # Whether the sizes above represent "inches" (numeric, e.g. 6, 8, 10)
    # or "sizes" (text, e.g. S, M, L, XL). Purely drives how the admin
    # dashboard renders/edits the size rows and picks an input type.
    variant_type = models.CharField(
        max_length=10, choices=VARIANT_TYPE_CHOICES, default="inches"
    )

    # Optional colors this product is available in, e.g. ["Blue", "Red"].
    # Completely optional — defaults to an empty list, meaning "no color
    # options", and the storefront simply hides the color swatches row
    # for any product with no colors.
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
        """[('6', 300), ('8', 500)] sorted by size number — for storefront
        display, so sizes always list smallest to largest."""
        if not self.size_prices:
            return []
        try:
            return sorted(self.size_prices.items(), key=lambda kv: float(kv[0]))
        except (ValueError, TypeError):
            return list(self.size_prices.items())

    @property
    def size_prices_json(self):
        """JSON string version, safe to drop into a data-* attribute in
        templates for the admin dashboard's Edit modal."""
        return json.dumps(self.size_prices or {})

    @property
    def color_list(self):
        """Plain Python list of color names, e.g. ["Blue", "Red"].
        Empty list if this product has no colors — always safe to
        iterate over in a template with {% if product.color_list %}.
        Defensively parses the stored value so this never breaks even
        if `colors` ever ends up as something other than a clean list."""
        return _safe_json_list(self.colors)

    @property
    def colors_json(self):
        """JSON string version, safe to drop into a data-* attribute in
        templates for the admin dashboard's Edit modal."""
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