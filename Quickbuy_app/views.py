from django.shortcuts import render
from .models import Product, Order


def home(request):
    products = Product.objects.all()
    orders = Order.objects.filter(status='paid').order_by('-created_at')
    return render(request, 'home.html', {'products': products, 'orders': orders})
