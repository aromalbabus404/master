import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .forms import ProductForm, HeroForm, SiteSettingsForm
from .models import (
    Product, GalleryImage, Review, ReviewMedia, Order, OrderItem,
    HeroSection, SiteSettings, CATEGORY_CHOICES,
)


# ---------------------------------------------------------------------------
# STOREFRONT (public)
# ---------------------------------------------------------------------------

def index(request):
    context = {
        "hero": HeroSection.load(),
        "settings": SiteSettings.load(),
        "products": Product.objects.all(),
        "gallery": GalleryImage.objects.all(),
        "reviews": Review.objects.filter(status="approved"),
        "categories": CATEGORY_CHOICES,
    }
    return render(request, "pools/index.html", context)


@csrf_protect
@require_POST
def submit_order(request):
    """Called via fetch() from the storefront checkout modal. Persists the
    order to the real database, then the browser opens WhatsApp itself."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        name = data["name"].strip()
        mobile = data["mobile"].strip()
        state = data["state"].strip()
        pincode = data["pincode"].strip()
        address = data["address"].strip()
        items = data["items"]
        total = int(data["total"])

        if not all([name, mobile, state, pincode, address]) or not items:
            return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

        order = Order.objects.create(
            name=name, mobile=mobile, state=state, pincode=pincode,
            address=address, total=total,
        )
        for it in items:
            OrderItem.objects.create(
                order=order,
                name=it["name"], size=it["size"], qty=int(it["qty"]), price=int(it["price"]),
            )
        return JsonResponse({"ok": True, "order_id": order.id})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


@csrf_protect
@require_POST
def submit_review(request):
    """Called via fetch() with multipart/form-data (name, rating, text, media[])."""
    name = request.POST.get("name", "").strip()
    text = request.POST.get("text", "").strip()
    rating = request.POST.get("rating", "5")

    if not name or not text:
        return JsonResponse({"ok": False, "error": "Missing name or review text"}, status=400)

    try:
        rating = max(1, min(5, int(rating)))
    except ValueError:
        rating = 5

    review = Review.objects.create(name=name, text=text, rating=rating, status="pending")

    for f in request.FILES.getlist("media"):
        ReviewMedia.objects.create(
            review=review, file=f, is_video=(f.content_type or "").startswith("video")
        )

    return JsonResponse({"ok": True, "review_id": review.id})


# ---------------------------------------------------------------------------
# ADMIN DASHBOARD (login required — real accounts via Django auth / createsuperuser)
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    context = {
        "products": Product.objects.all(),
        "gallery": GalleryImage.objects.all(),
        "reviews": Review.objects.all(),
        "orders": Order.objects.prefetch_related("items").all(),
        "hero": HeroSection.load(),
        "settings": SiteSettings.load(),
        "hero_form": HeroForm(instance=HeroSection.load()),
        "settings_form": SiteSettingsForm(instance=SiteSettings.load()),
        "product_form": ProductForm(),
        "categories": CATEGORY_CHOICES,
        "stat_products": Product.objects.count(),
        "stat_gallery": GalleryImage.objects.count(),
        "stat_pending": Review.objects.filter(status="pending").count(),
        "stat_orders": Order.objects.count(),
    }
    return render(request, "pools/dashboard.html", context)


@login_required
@require_POST
def hero_save(request):
    hero = HeroSection.load()
    form = HeroForm(request.POST, instance=hero)
    if form.is_valid():
        form.save()
        messages.success(request, "Hero section saved.")
    else:
        messages.error(request, f"Could not save hero section: {form.errors.as_text()}")
    return redirect("dashboard")


@login_required
@require_POST
def settings_save(request):
    settings_obj = SiteSettings.load()
    form = SiteSettingsForm(request.POST, instance=settings_obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Settings saved.")
    else:
        messages.error(request, "Could not save settings.")
    return redirect("dashboard")


@login_required
@require_POST
def product_save(request, pk=None):
    instance = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST, request.FILES, instance=instance)
    if form.is_valid():
        form.save()
        messages.success(request, "Product updated." if pk else "Product added.")
    else:
        messages.error(request, f"Could not save product: {form.errors.as_text()}")
    return redirect("dashboard")


@login_required
@require_POST
def product_delete(request, pk):
    get_object_or_404(Product, pk=pk).delete()
    messages.success(request, "Product deleted.")
    return redirect("dashboard")


@login_required
@require_POST
def gallery_add(request):
    url = request.POST.get("image_url", "").strip()
    file = request.FILES.get("image_file")
    if not url and not file:
        messages.error(request, "Add an image URL or upload a file.")
        return redirect("dashboard")
    GalleryImage.objects.create(image_url=url or None, image_file=file or None)
    messages.success(request, "Image added to gallery.")
    return redirect("dashboard")


@login_required
@require_POST
def gallery_delete(request, pk):
    get_object_or_404(GalleryImage, pk=pk).delete()
    messages.success(request, "Gallery image deleted.")
    return redirect("dashboard")


@login_required
@require_POST
def review_set_status(request, pk, status):
    if status not in ("approved", "rejected", "pending"):
        messages.error(request, "Invalid status.")
        return redirect("dashboard")
    review = get_object_or_404(Review, pk=pk)
    review.status = status
    review.save()
    messages.success(request, f"Review marked {status}.")
    return redirect("dashboard")
