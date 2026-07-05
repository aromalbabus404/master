import json
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
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

        # Re-validate each item's price against the product's real size_prices,
        # so a tampered price from devtools can never be saved as an order.
        validated_total = 0
        for it in items:
            product = Product.objects.filter(name=it["name"]).first()
            size = str(it.get("size", "")).strip()
            claimed_price = int(it["price"])

            if product and product.size_prices:
                real_price = product.size_prices.get(size)
                if real_price is not None:
                    claimed_price = int(real_price)

            it["price"] = claimed_price
            validated_total += claimed_price * int(it["qty"])

        order = Order.objects.create(
            name=name, mobile=mobile, state=state, pincode=pincode,
            address=address, total=validated_total,
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



def admin_login(request):
    # Already logged in
    if request.user.is_authenticated:   
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password.")

    return render(request, "registration/login.html")


# ----------------------------
# LOGOUT
# ----------------------------
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


@login_required
@require_POST
def hero_save(request):
    hero = HeroSection.load()

    form = HeroForm(
        request.POST,
        request.FILES,
        instance=hero,
    )

    if form.is_valid():
        hero = form.save(commit=False)

        # Save uploaded video
        if request.FILES.get("video_file"):
            hero.video_file = request.FILES["video_file"]
            hero.video_url = ""

        # Save uploaded poster image
        if request.FILES.get("poster_image_file"):
            hero.poster_image_file = request.FILES["poster_image_file"]
            hero.poster_image = ""

        hero.save()

        # Update URL fields after Cloudinary upload
        if hero.video_file:
            hero.video_url = hero.video_file.build_url(resource_type="video")

        if hero.poster_image_file:
            hero.poster_image = hero.poster_image_file.build_url()

        hero.save(update_fields=[
            "video_url",
            "poster_image",
        ])

        messages.success(request, "Hero section updated successfully.")

    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

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


def _parse_size_prices(request):
    """Reads size[] and price[] arrays submitted from the dynamic
    'Add Size' rows and returns a clean dict like {"6": 300.0, "8": 500.0},
    skipping any incomplete rows."""
    sizes = request.POST.getlist("size[]")
    prices = request.POST.getlist("price[]")
    size_prices = {}
    for size, price in zip(sizes, prices):
        size = size.strip()
        price = price.strip()
        if not size or not price:
            continue
        try:
            size_prices[size] = float(price)
        except ValueError:
            continue
    return size_prices


def _parse_colors(request):
    """Reads the color[] array submitted from the dynamic 'Add Color' rows.
    Colors are entirely OPTIONAL — empty/blank rows are silently skipped,
    duplicates are dropped, and if nothing was entered this simply returns
    an empty list (which is a perfectly valid, expected result)."""
    raw_colors = request.POST.getlist("color[]")
    colors = []
    for c in raw_colors:
        c = c.strip()
        if not c:
            continue
        if c not in colors:
            colors.append(c)
    return colors


def _parse_variant_type(request):
    """'inches' or 'sizes' — defaults to 'inches' if not sent/invalid."""
    vtype = request.POST.get("variant_type", "inches").strip().lower()
    return vtype if vtype in ("inches", "sizes") else "inches"


@login_required
@require_POST
def product_save(request, pk=None):
    """Handles both Add Product (pk=None) and any legacy full-form edit."""
    instance = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST, request.FILES, instance=instance)
    if form.is_valid():
        product = form.save(commit=False)

        size_prices = _parse_size_prices(request)
        if size_prices:
            product.size_prices = size_prices
            # Keep legacy fields in sync so any old code/templates still work
            product.sizes = ", ".join(f'{s}"' for s in size_prices.keys())
            product.price = min(size_prices.values())
        elif not pk:
            messages.error(request, "Please add at least one size and price.")
            return redirect("dashboard")

        product.variant_type = _parse_variant_type(request)

        # Colors are optional — an empty list is a valid, expected value.
        product.colors = _parse_colors(request)

        product.save()
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


import os

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE_MB = 5


@login_required
@require_POST
def gallery_add(request):
    url = request.POST.get("image_url", "").strip()
    file = request.FILES.get("image_file")

    if not url and not file:
        messages.error(request, "Add an image URL or upload a file.")
        return redirect("dashboard")

    if file:
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            messages.error(request, "Unsupported file type. Please upload a JPG, PNG, WEBP, or GIF image.")
            return redirect("dashboard")

        if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            messages.error(request, f"Image is too large. Max size is {MAX_IMAGE_SIZE_MB}MB.")
            return redirect("dashboard")

        if not file.content_type or not file.content_type.startswith("image/"):
            messages.error(request, "The uploaded file does not appear to be a valid image.")
            return redirect("dashboard")

    gallery = GalleryImage()

    if file:
        gallery.image_file = file
    elif url:
        gallery.image_url = url

    try:
        gallery.save()
    except Exception:
        messages.error(request, "Something went wrong while saving the image. Please try again.")
        return redirect("dashboard")

    messages.success(request, "Gallery image uploaded.")
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


def shop(request):
    query = request.GET.get("q", "")

    products = Product.objects.all()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(badge__icontains=query) |
            Q(sizes__icontains=query)
        )

    return render(request, "pools/shop.html", {
        "products": products,
        "query": query,
        "settings": SiteSettings.load(),
    })


@login_required
@require_POST
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    product.name = request.POST.get("name")
    product.category = request.POST.get("category")
    product.badge = request.POST.get("badge")
    product.mrp = request.POST.get("mrp") or None
    product.image_url = request.POST.get("image_url")

    size_prices = _parse_size_prices(request)
    if size_prices:
        product.size_prices = size_prices
        product.sizes = ", ".join(f'{s}"' for s in size_prices.keys())
        product.price = min(size_prices.values())

    product.variant_type = _parse_variant_type(request)

    # Colors are optional — saving an empty list clears any previously set colors.
    product.colors = _parse_colors(request)

    if request.FILES.get("image_file"):
        product.image_file = request.FILES["image_file"]

    product.save()

    messages.success(request, "Product updated successfully.")
    return redirect("dashboard")