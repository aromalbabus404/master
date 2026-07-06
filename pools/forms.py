from django import forms
from .models import Product, HeroSection, SiteSettings


IMAGE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/octet-stream",  # Some browsers upload HEIC with this type
]


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "badge",
            "mrp",
            "image_url",
            "image_file",
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "badge": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Bestseller",
            }),
            "mrp": forms.NumberInput(attrs={"class": "form-control"}),
            "image_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://...",
            }),
            "image_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*,.heic,.heif",
            }),
        }

    def clean(self):
        cleaned = super().clean()

        if (
            not cleaned.get("image_url")
            and not cleaned.get("image_file")
            and not (self.instance and self.instance.image_file)
        ):
            raise forms.ValidationError(
                "Please upload an image or provide an image URL."
            )

        return cleaned

    def clean_image_file(self):
        image = self.cleaned_data.get("image_file")

        if not image:
            return image

        if not hasattr(image, "size"):
            return image

        max_size = 20 * 1024 * 1024  # 20 MB

        if image.size > max_size:
            raise forms.ValidationError(
                "Image must be smaller than 20 MB."
            )

        if hasattr(image, "content_type"):
            ct = image.content_type.lower()

            if ct not in IMAGE_TYPES and not ct.startswith("image/"):
                raise forms.ValidationError(
                    "Supported image formats: JPG, JPEG, PNG, WEBP, HEIC and HEIF."
                )

        return image


class HeroForm(forms.ModelForm):
    """Text-only now — the hero video/poster image are static files shipped
    with the project (static/pools/hero.mp4, static/pools/hero-poster.jpg),
    not managed through this form or the dashboard."""

    class Meta:
        model = HeroSection

        fields = [
            "eyebrow",
            "heading",
            "sub",
            "stat1_value",
            "stat1_label",
            "stat2_value",
            "stat2_label",
            "stat3_value",
            "stat3_label",
            "stat4_value",
            "stat4_label",
        ]

        widgets = {
            "eyebrow": forms.TextInput(attrs={"class": "form-control"}),

            "heading": forms.TextInput(attrs={"class": "form-control"}),

            "sub": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),

            "stat1_value": forms.TextInput(attrs={"class": "form-control"}),
            "stat1_label": forms.TextInput(attrs={"class": "form-control"}),

            "stat2_value": forms.TextInput(attrs={"class": "form-control"}),
            "stat2_label": forms.TextInput(attrs={"class": "form-control"}),

            "stat3_value": forms.TextInput(attrs={"class": "form-control"}),
            "stat3_label": forms.TextInput(attrs={"class": "form-control"}),

            "stat4_value": forms.TextInput(attrs={"class": "form-control"}),
            "stat4_label": forms.TextInput(attrs={"class": "form-control"}),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["admin_whatsapp"]

        widgets = {
            "admin_whatsapp": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "917356462150",
                }
            )
        }