from django.contrib import admin
from .models import Product, GalleryImage, Review, ReviewMedia, Order, OrderItem, HeroSection, SiteSettings


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "mrp", "badge", "created_at")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")


class ReviewMediaInline(admin.TabularInline):
    model = ReviewMedia
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    inlines = [ReviewMediaInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "mobile", "total", "created_at")
    inlines = [OrderItemInline]


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    pass


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    pass
