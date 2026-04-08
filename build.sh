#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Seed products if they don't exist
python manage.py shell -c "
from Quickbuy_app.models import Product
data = [
    ('Smart Watch', 'Sleek smartwatch with health tracking and 7-day battery.', 149.99, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400'),
    ('Wireless Earbuds', 'Premium noise-cancelling earbuds with 30-hour playtime.', 89.99, 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400'),
    ('Gaming Mouse', 'High-precision gaming mouse with RGB and 16000 DPI.', 59.99, 'https://images.unsplash.com/photo-1527814050087-3793815479db?w=400'),
]
for name, desc, price, img in data:
    obj, created = Product.objects.get_or_create(name=name, defaults={'description': desc, 'price': price, 'image_url': img})
    print(f'{'Created' if created else 'Already exists'}: {name}')
print('Done!')
"
