from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from .models import Product, Order


def home(request):
    products = Product.objects.all()
    orders = Order.objects.filter(status='paid').order_by('-created_at')
    return render(request, 'home.html', {'products': products, 'orders': orders})


@require_POST
def create_checkout_session(request):
    # Will be implemented in Step 6
    return HttpResponse("Stripe checkout coming in Step 6", status=501)


def payment_success(request):
    # Will be implemented in Step 7
    return HttpResponse("Payment success coming in Step 7", status=501)


def payment_cancel(request):
    # Will be implemented in Step 7
    return redirect('home')
