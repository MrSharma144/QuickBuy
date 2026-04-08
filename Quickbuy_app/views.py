from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseRedirect
import stripe

from .models import Product, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


# ─────────────────────────────────────────────
# Home
# ─────────────────────────────────────────────
def home(request):
    products = Product.objects.all()
    orders = []
    if request.user.is_authenticated:
        orders = Order.objects.filter(
            user=request.user, status='paid'
        ).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'home.html', {'products': products, 'orders': orders})


# ─────────────────────────────────────────────
# Auth — Signup
# ─────────────────────────────────────────────
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})


# ─────────────────────────────────────────────
# Auth — Login
# ─────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


# ─────────────────────────────────────────────
# Auth — Logout
# ─────────────────────────────────────────────
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ─────────────────────────────────────────────
# Stripe Checkout
# ─────────────────────────────────────────────
@require_POST
def create_checkout_session(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'Please log in to proceed with checkout.')
        return redirect('login')

    # Single DB query — fetch all products into a dict for O(1) lookups
    products = {p.id: p for p in Product.objects.all()}

    line_items = []
    cart = {}  # { product_id: quantity }

    for pid, product in products.items():
        qty = int(request.POST.get(f'quantity_{pid}', 0))
        if qty > 0:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'description': product.description,
                    },
                    'unit_amount': product.price_in_cents(),
                },
                'quantity': qty,
            })
            cart[pid] = qty

    if not line_items:
        messages.warning(request, 'Please add at least one item before checking out.')
        return redirect('home')

    base_url = request.build_absolute_uri('/').rstrip('/')
    success_url = f"{base_url}/payment/success/?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url  = f"{base_url}/payment/cancel/"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('home')

    # Calculate total locally — no extra DB queries
    total = sum(products[pid].price * qty for pid, qty in cart.items())

    order = Order.objects.create(
        user=request.user,
        stripe_checkout_id=session.id,
        total_amount=total,
        status='pending',
    )

    # Bulk-create order items — one INSERT instead of N
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=products[pid],
            quantity=qty,
            unit_price=products[pid].price,
        )
        for pid, qty in cart.items()
    ])

    # HTTP 303 See Other — browser uses GET on redirect, no POST resubmission
    response = HttpResponseRedirect(session.url)
    response.status_code = 303
    return response


# ─────────────────────────────────────────────
# Payment Success
# ─────────────────────────────────────────────
def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('home')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        messages.error(request, 'Could not verify payment. Contact support.')
        return redirect('home')

    order = get_object_or_404(Order, stripe_checkout_id=session_id)

    # Idempotent — only update once even if this URL is hit multiple times
    if session.payment_status == 'paid' and order.status != 'paid':
        order.status = 'paid'
        order.save()

    messages.success(request, f'🎉 Payment successful! Order #{order.id} confirmed.')
    return redirect('home')


# ─────────────────────────────────────────────
# Payment Cancel
# ─────────────────────────────────────────────
def payment_cancel(request):
    session_id = request.GET.get('session_id')
    if session_id:
        Order.objects.filter(stripe_checkout_id=session_id, status='pending').delete()

    messages.warning(request, 'Payment cancelled. Your cart was not charged.')
    return redirect('home')
