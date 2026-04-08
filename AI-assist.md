# AI Assistance Disclosure — QuickBuy

This document outlines the specific areas where AI tooling (GitHub Copilot / ChatGPT) was used during the development of this project. The majority of the project — architecture decisions, Django setup, Stripe integration logic, database design, and deployment config — was planned and implemented by me.

---

## What I Built Myself

- Designed the full project architecture (Django app structure, URL routing, model relationships)
- Chose Stripe Checkout over Payment Intents and understood the trade-offs
- Implemented the `Order` / `OrderItem` / `Product` models and their relationships
- Wrote all the core views: checkout session creation, success/cancel handling, auth views
- Set up the environment variable strategy (SQLite locally, Postgres via `DATABASE_URL` in production)
- Handled double-submit protection logic — idempotent success view, `unique` DB constraint, `@require_POST`
- Configured Django's built-in auth system (login, logout, signup using `UserCreationForm`)
- Set up `python-dotenv` and connected it to `settings.py`
- Wrote all URL patterns and wired up the project-level and app-level `urls.py`

---

## Where I Used AI Assistance

### 1. Bootstrap CSS — Card Hover Effects & Gradient Styling

I knew the layout I wanted but used AI to quickly generate the CSS for smooth hover transitions on the product cards and the gradient button styling, rather than writing the keyframe/transition values by hand.

**Files affected:** `templates/base.html` (the `<style>` block — `.product-card:hover`, `.btn-buy`, `.order-card` styles)

```css
/* AI helped generate this hover transition snippet */
.product-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 50px rgba(108, 99, 255, 0.18) !important;
}
```

---

### 2. `DATABASE_URL` Parsing Logic

I knew I wanted SQLite locally and Postgres in production. I used AI to get the `urllib.parse` snippet that correctly parses a Postgres connection string from the `DATABASE_URL` environment variable without needing an extra library like `dj-database-url`.

**File affected:** `Quickbuy_project/settings.py`

```python
# AI suggested this urlparse approach to avoid adding dj-database-url as a dependency
import urllib.parse
url = urllib.parse.urlparse(DATABASE_URL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': url.path[1:],
        ...
    }
}
```

---

### 3. JavaScript — Live Cart Summary & +/− Quantity Buttons

I implemented the quantity input logic myself, but used AI to help write the JavaScript that dynamically updates the "Buy Now — $X.XX" button label as quantities change, since it's a UI polish detail rather than core logic.

**File affected:** `templates/home.html` (the `{% block extra_js %}` section)

```js
// AI helped write the live total update loop
document.querySelectorAll('.qty-field').forEach(input => {
    input.addEventListener('input', updateSummary);
});
```

---

### 4. `.gitignore` Template

Used AI to generate a comprehensive Python/Django `.gitignore` rather than writing one from scratch. I reviewed and confirmed the entries were appropriate.

**File affected:** `.gitignore`

---

## Summary

| Area | Done By |
|---|---|
| Django project setup & configuration | Me |
| Model design (Product, Order, OrderItem) | Me |
| Stripe Checkout integration | Me |
| Double-submit protection strategy | Me |
| User authentication (login / signup / logout) | Me |
| URL routing & view logic | Me |
| Environment variable strategy | Me |
| Bootstrap layout & page structure | Me |
| Card hover CSS & gradient button styles | AI-assisted |
| `DATABASE_URL` parsing snippet | AI-assisted |
| Live cart JS (qty update → button label) | AI-assisted |
| `.gitignore` file | AI-generated, reviewed by me |
