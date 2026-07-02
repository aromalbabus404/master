# AquaCraft Pools — Django + SQLite

This replaces the old `localStorage`-based prototype with a **real backend**:
every product, gallery image, review, order, hero-section edit, and setting
is now a row in an actual SQLite database (`db.sqlite3`), written and read
through Django. That means:

- Data is shared across every visitor and every admin — not stuck in one browser.
- Orders and review submissions from the storefront are permanently saved.
- The admin dashboard requires a real login (Django user accounts), not just
  "whoever has the URL."

## 1. Setup

```bash
cd aquacraft_django
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate        # creates db.sqlite3 with all tables
python manage.py seed_demo_data # optional: adds the 3 demo products + gallery images
python manage.py createsuperuser  # create your real admin login
```

## 2. Run it

```bash
python manage.py runserver
```

- Storefront: http://127.0.0.1:8000/
- Admin dashboard (custom, matches your original design): http://127.0.0.1:8000/dashboard/
- Login page: http://127.0.0.1:8000/login/
- Django's built-in admin (bonus, good for bulk edits): http://127.0.0.1:8000/admin/

Log in with the superuser you created in step 1.

## 3. What's in the database

| Model         | Replaces this localStorage key |
|---------------|--------------------------------|
| `HeroSection` | `ac_hero`                      |
| `Product`     | `ac_products`                  |
| `GalleryImage`| `ac_gallery`                   |
| `Review` / `ReviewMedia` | `ac_reviews`         |
| `Order` / `OrderItem`    | `ac_orders`          |
| `SiteSettings`| `ac_settings`                  |

## 4. How the pieces talk to each other

- **Storefront** (`pools/templates/pools/index.html`) — products, gallery,
  hero text, and approved reviews are rendered server-side from the
  database on every page load. The shopping cart itself still lives in
  browser memory for the session (that's normal — a cart isn't meant to be
  permanent), but **checkout POSTs the order to `/api/orders/`**, which
  saves it to the database before opening WhatsApp. Same for the review
  form → `/api/reviews/`.
- **Admin dashboard** (`pools/templates/pools/dashboard.html`) — every
  "Save" / "Add" / "Delete" / "Approve" button submits a real form to a
  Django view, which writes to the database and redirects back. No
  JavaScript is holding your data — refreshing the page never loses
  anything.

## 5. Adding more admin users

```bash
python manage.py createsuperuser
```
Any user created this way (superuser or regular staff, since the dashboard
only checks `login_required`) can log in and manage the site.

## 6. Going to production

Before deploying for real:
- Set a real `SECRET_KEY` in `aquacraft/settings.py` (currently a placeholder).
- Set `DEBUG = False` and a real `ALLOWED_HOSTS` list.
- Swap SQLite for Postgres if you expect concurrent write-heavy traffic
  (SQLite is genuinely fine for a small business site's read-heavy,
  low-order-volume traffic).
- Serve `MEDIA_ROOT` (uploaded images) via your web server or a bucket like S3 —
  Django's dev server only serves it because `DEBUG=True`.
- Put it behind Gunicorn/Nginx or a platform like Render/Railway/PythonAnywhere.
