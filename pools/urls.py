from django.urls import path
from . import views

urlpatterns = [
    # Storefront
    path("", views.index, name="index"),
    path("shop/", views.shop, name="shop"),
    path("api/orders/", views.submit_order, name="submit_order"),
    path("api/reviews/", views.submit_review, name="submit_review"),

    # Legacy standalone product edit endpoint (kept for backward compatibility,
    # renamed so it no longer collides with the dashboard's "product_edit" name)
    path("product/<int:pk>/edit/", views.product_edit, name="product_edit_legacy"),
    
    
    path("hero/remove/", views.hero_remove_file, name="hero_remove_file"),
    # Admin dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/hero/save/", views.hero_save, name="hero_save"),
    path("dashboard/settings/save/", views.settings_save, name="settings_save"),
    path("dashboard/products/add/", views.product_save, name="product_add"),
    path("dashboard/products/<int:pk>/edit/", views.product_save, name="product_edit"),
    path("dashboard/products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("dashboard/gallery/add/", views.gallery_add, name="gallery_add"),
    path("dashboard/gallery/<int:pk>/delete/", views.gallery_delete, name="gallery_delete"),
    path("dashboard/reviews/<int:pk>/<str:status>/", views.review_set_status, name="review_set_status"),
]