from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse
import stripe

from .models import Product, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def home(request):
    products = Product.objects.all()
    orders = Order.objects.filter(status='paid').order_by('-created_at')
    return render(request, 'home.html', {'products': products, 'orders': orders})


@require_POST
def create_checkout_session(request):
    products = Product.objects.all()

    # Build line items from form quantities
    line_items = []
    cart = {}  # { product_id: quantity }

    for product in products:
        qty = int(request.POST.get(f'quantity_{product.id}', 0))
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
            cart[product.id] = qty

    # Guard: nothing selected
    if not line_items:
        messages.warning(request, 'Please add at least one item before checking out.')
        return redirect('home')

    # Build absolute URLs for Stripe redirect
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

    # Calculate total amount locally
    total = sum(
        Product.objects.get(pk=pid).price * qty
        for pid, qty in cart.items()
    )

    # Create a PENDING order (will be marked paid on success)
    order = Order.objects.create(
        stripe_checkout_id=session.id,
        total_amount=total,
        status='pending',
    )

    # Save order items
    for pid, qty in cart.items():
        product = Product.objects.get(pk=pid)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=qty,
            unit_price=product.price,
        )

    return redirect(session.url, permanent=False)


def payment_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('home')

    try:
        # Retrieve session from Stripe to verify payment
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        messages.error(request, 'Could not verify payment. Contact support.')
        return redirect('home')

    # Mark order as paid (idempotent – safe on refresh)
    order = get_object_or_404(Order, stripe_checkout_id=session_id)

    if session.payment_status == 'paid' and order.status != 'paid':
        order.status = 'paid'
        order.save()

    messages.success(request, f'🎉 Payment successful! Order #{order.id} confirmed.')
    return redirect('home')


def payment_cancel(request):
    # Delete the pending order so it doesn't pollute the DB
    session_id = request.GET.get('session_id')
    if session_id:
        Order.objects.filter(stripe_checkout_id=session_id, status='pending').delete()

    messages.warning(request, 'Payment cancelled. Your cart was not charged.')
    return redirect('home')
