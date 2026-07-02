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
            "eyebrow", "heading", "sub", "video_url", "poster_image",
            "stat1_value", "stat1_label", "stat2_value", "stat2_label",
            "stat3_value", "stat3_label", "stat4_value", "stat4_label",
        ]
        widgets = {f: forms.TextInput(attrs={"class": "form-control"}) for f in [
            "eyebrow", "heading", "video_url", "poster_image",
            "stat1_value", "stat1_label", "stat2_value", "stat2_label",
            "stat3_value", "stat3_label", "stat4_value", "stat4_label",
        ]}
        widgets["sub"] = forms.Textarea(attrs={"class": "form-control", "rows": 2})


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ["admin_whatsapp"]
        widgets = {"admin_whatsapp": forms.TextInput(attrs={"class": "form-control", "placeholder": "917356462150"})}
