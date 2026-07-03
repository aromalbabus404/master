from django import forms
from .models import Product, HeroSection, SiteSettings, CATEGORY_CHOICES


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "badge", "price", "mrp", "sizes", "image_url", "image_file"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "badge": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Bestseller"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "mrp": forms.NumberInput(attrs={"class": "form-control"}),
            "sizes": forms.TextInput(attrs={"class": "form-control", "placeholder": "20x10 ft, 25x12 ft"}),
            "image_url": forms.TextInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "image_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("image_url") and not cleaned.get("image_file") and not (
            self.instance and self.instance.image_file
        ):
            raise forms.ValidationError("Add an image URL or upload an image file.")
        return cleaned

class HeroForm(forms.ModelForm):
    class Meta:
        model = HeroSection
        fields = [
            "eyebrow",
            "heading",
            "sub",

            "video_url",
            "poster_image",

            "video_file",
            "poster_image_file",

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

            "video_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "poster_image": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "video_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "video/*",
            }),

            "poster_image_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*",
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

    # -------------------------
    # Validate uploaded video
    # -------------------------
    def clean_video_file(self):
        video = self.cleaned_data.get("video_file")

        if video:
            # Cloudinary free limit = 10MB
            max_size = 10 * 1024 * 1024

            if video.size > max_size:
                raise forms.ValidationError(
                    "Video must be smaller than 10 MB."
                )

            if not video.content_type.startswith("video/"):
                raise forms.ValidationError(
                    "Please upload a valid video."
                )

        return video

    # -------------------------
    # Validate uploaded image
    # -------------------------
    def clean_poster_image_file(self):
        image = self.cleaned_data.get("poster_image_file")

        if image:
            max_size = 5 * 1024 * 1024

            if image.size > max_size:
                raise forms.ValidationError(
                    "Image must be smaller than 5 MB."
                )

            if not image.content_type.startswith("image/"):
                raise forms.ValidationError(
                    "Please upload a valid image."
                )

        return image

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["admin_whatsapp"]
        widgets = {"admin_whatsapp": forms.TextInput(attrs={"class": "form-control", "placeholder": "917356462150"})}
