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

VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-msvideo",
    "video/mpeg",
    "video/3gpp",
    "video/x-matroska",
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
                "placeholder": "https://...",
            }),

            "poster_image": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://...",
            }),

            "video_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "video/*",
            }),

            "poster_image_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/*,.heic,.heif",
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

    def clean_video_file(self):
        video = self.cleaned_data.get("video_file")

        if not video:
            return video

        if not hasattr(video, "size"):
            return video

        max_size = 30 * 1024 * 1024  # 30 MB

        if video.size > max_size:
            raise forms.ValidationError(
                "Video must be smaller than 30 MB."
            )

        if hasattr(video, "content_type"):
            ct = video.content_type.lower()

            if ct not in VIDEO_TYPES and not ct.startswith("video/"):
                raise forms.ValidationError(
                    "Please upload a valid video."
                )

        return video

    def clean_poster_image_file(self):
        image = self.cleaned_data.get("poster_image_file")

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