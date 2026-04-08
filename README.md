# QuickBuy 🛍️

A Django-based e-commerce app where users can browse 3 fixed products, enter quantities, pay with Stripe (test mode), and view their order history — all on a single page.

⏱️ **Development Time:** Built in 5-6 hours.
---

## Live Demo Flow

1. Sign up or log in
2. Set quantities on the product cards
3. Click **Buy Now** → redirected to Stripe's hosted checkout
4. Pay with test card `4242 4242 4242 4242`
5. Land back on the home page with your order in **My Orders**

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Django 6.x | Batteries-included ORM, auth, CSRF, sessions out of the box |
| **Database** | SQLite (local) / PostgreSQL (production) | Zero-config locally; production-ready switch via `DATABASE_URL` |
| **Payments** | Stripe Checkout (hosted page) | No custom card form needed — Stripe handles PCI, 3DS, Apple Pay |
| **Frontend** | Bootstrap 5 + vanilla JS | Simple, responsive, no build step required |
| **Fonts** | Google Fonts (Inter) | Clean, modern sans-serif |
| **Icons** | Bootstrap Icons | Consistent icon set with no extra JS |
| **Environment** | python-dotenv | Loads `.env` file into `os.environ` at startup |

---

## Framework Rationale

### Why Django?

- **ORM + migrations** — models map directly to DB tables; schema changes are versioned
- **Built-in auth** — `User`, `login()`, `logout()`, `UserCreationForm` require zero extra libraries
- **CSRF protection** — built in; every POST form is protected by default
- **Admin panel** — products and orders are manageable at `/admin/` instantly
- **Template engine** — server-rendered HTML; no separate frontend build pipeline

### Why Stripe Checkout over Payment Intents?

Stripe Checkout is a **hosted payment page** — Stripe handles the card form, validation, 3D Secure, Apple Pay, Google Pay, and error states. We only need ~15 lines of Python.

Payment Intents would require 100+ lines of JavaScript, custom card HTML, 3DS confirmation handling, and more. For a 48-hour MVP with 3 products, Checkout is the right choice.

See [`AI-assist.md`](AI-assist.md) for more details.

---

## Project Structure

```
QuickBuy/
├── Quickbuy_project/        # Django project config
│   ├── settings.py          # All settings; env vars loaded here
│   ├── urls.py              # Root URL dispatcher
│   └── wsgi.py
├── Quickbuy_app/            # Main application
│   ├── models.py            # Product, Order, OrderItem
│   ├── views.py             # All views (home, auth, checkout, success)
│   ├── urls.py              # App-level URL patterns
│   ├── admin.py             # Admin registrations
│   └── migrations/          # Database migrations
├── templates/               # HTML templates
│   ├── base.html            # Shared layout, navbar, Bootstrap, styles
│   ├── home.html            # Product cards + My Orders
│   ├── login.html           # Login form
│   ├── signup.html          # Signup form
│   └── 403.html             # Custom CSRF/forbidden error page
├── .env                     # Local secrets (NOT committed)
├── .env.example             # Template for env vars
├── AI-assist.md             # AI tool disclosure
├── manage.py
└── requirements.txt
```

---

## Data Models

```
Product
  ├── name (CharField)
  ├── description (TextField)
  ├── price (DecimalField)
  └── image_url (URLField)

Order
  ├── user (FK → User, nullable)
  ├── stripe_checkout_id (CharField, UNIQUE)
  ├── total_amount (DecimalField)
  ├── status  [ pending | paid | cancelled ]
  └── created_at (DateTimeField)

OrderItem
  ├── order (FK → Order)
  ├── product (FK → Product)
  ├── quantity (PositiveIntegerField)
  └── unit_price (DecimalField)  ← snapshot at time of purchase
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `DEBUG` | ✅ | `True` locally, `False` in production |
| `SECRET_KEY` | ✅ | Django secret key — keep private |
| `ALLOWED_HOSTS` | ✅ | Comma-separated (e.g., `127.0.0.1,localhost`) |
| `STRIPE_PUBLISHABLE_KEY` | ✅ | From Stripe Dashboard → Developers → API Keys |
| `STRIPE_SECRET_KEY` | ✅ | From Stripe Dashboard → Developers → API Keys |
| `DATABASE_URL` | ⬜ | Optional. Set for Postgres in production (e.g. `postgres://user:pass@host:5432/db`) |

> **Note:** If `DATABASE_URL` is not set, SQLite is used automatically.

---

## How to Run Locally — Step by Step

### Prerequisites

- Python 3.10+
- pip
- A free [Stripe account](https://dashboard.stripe.com/register) (test mode keys)

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/MrSharma144/QuickBuy.git
cd QuickBuy
```

---

### Step 2 — Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:

```bash
pip install django stripe psycopg2-binary python-dotenv
```

---

### Step 4 — Set up environment variables

```bash
# Windows (copy)
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in:

```env
DEBUG=True
SECRET_KEY=any-random-string-here
ALLOWED_HOSTS=127.0.0.1,localhost

STRIPE_PUBLISHABLE_KEY=pk_test_...   ← from Stripe Dashboard
STRIPE_SECRET_KEY=sk_test_...        ← from Stripe Dashboard
```

> Get your test keys from: https://dashboard.stripe.com/test/apikeys

---

### Step 5 — Apply database migrations

```bash
python manage.py migrate
```

This creates `db.sqlite3` with all tables.

---

### Step 6 — Seed the 3 fixed products

> The seed command is removed from the project. Run this one-time snippet instead:

```bash
python manage.py shell -c "
from Quickbuy_app.models import Product
Product.objects.get_or_create(name='Smart Watch', defaults={'description':'Sleek smartwatch with health tracking and 7-day battery.','price':149.99,'image_url':'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400'})
Product.objects.get_or_create(name='Wireless Earbuds', defaults={'description':'Premium noise-cancelling earbuds with 30-hour playtime.','price':89.99,'image_url':'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400'})
Product.objects.get_or_create(name='Gaming Mouse', defaults={'description':'High-precision gaming mouse with RGB and 16000 DPI.','price':59.99,'image_url':'https://images.unsplash.com/photo-1527814050087-3793815479db?w=400'})
print('Products seeded!')
"
```

---

### Step 7 — Create an admin user (optional)

```bash
python manage.py createsuperuser
```

Access the admin at: `http://127.0.0.1:8000/admin/`

---

### Step 8 — Start the development server

```bash
python manage.py runserver
```

Open your browser at: **`http://127.0.0.1:8000/`**

---

## Testing a Payment

Use Stripe's test card details:

| Field | Value |
|---|---|
| Card number | `4242 4242 4242 4242` |
| Expiry | Any future date (e.g. `12/26`) |
| CVC | Any 3 digits (e.g. `123`) |
| Name / ZIP | Anything |

---

## URL Reference

| URL | Method | Description |
|---|---|---|
| `/` | GET | Home page — products + My Orders |
| `/signup/` | GET, POST | Create a new account |
| `/login/` | GET, POST | Log in |
| `/logout/` | GET | Log out and redirect to login |
| `/create-checkout-session/` | POST | Create Stripe session, redirect to Stripe |
| `/payment/success/` | GET | Called by Stripe on successful payment |
| `/payment/cancel/` | GET | Called by Stripe when user cancels |
| `/admin/` | GET | Django admin panel |

---

## Double-Submit Protection

The app uses 7 layers to prevent double charges and duplicate orders:

1. **JS disables the Buy button** on submit (prevents double-click)
2. **JS blocks empty cart submission** (all quantities = 0)
3. **`@require_POST`** — checkout URL rejects GET requests
4. **Server-side empty cart check** — even if JS is bypassed
5. **`unique` DB constraint** on `stripe_checkout_id` — one Order per session
6. **Idempotent success view** — `if order.status != 'paid'` guard prevents double-update on refresh
7. **Stripe single-use sessions** — Stripe rejects re-payment on the same session

See [`double_submit_protection.md`](double_submit_protection.md) for full details and flow diagram.

---

## Switching to PostgreSQL (Production)

Set `DATABASE_URL` in your production environment:

```env
DATABASE_URL=postgres://username:password@hostname:5432/database_name
```

Django will automatically switch from SQLite to PostgreSQL. No other change is needed.

---

## Contributing / Notes

- All sensitive keys are in `.env` which is in `.gitignore` — never commit it
- `.env.example` is committed as a template for other developers
- Run `python manage.py check` to verify configuration before starting the server
