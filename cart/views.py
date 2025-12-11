from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import CartItem, Order, OrderItem
from products.models import Product
from payment.models import Payment
import razorpay
from django.conf import settings
from datetime import date, timedelta
from django.utils.dateparse import parse_date

# Create your views here.
@login_required(login_url='/accounts/login/')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        duration = request.POST.get('duration')

        today = date.today()

        if duration == '1_day':
            start = today
            end = today
        elif duration == '1_week':
            start = today
            end = today + timedelta(days=6)
        elif duration == '1_month':
            start = today
            end = today + timedelta(days=29)
        elif duration == 'custom':
            start = parse_date(request.POST.get('start_date'))
            end = parse_date(request.POST.get('end_date'))
        else:
            start = today
            end = today

        total_days = (end - start).days + 1
        total_price = product.price * quantity * total_days

        CartItem.objects.create(
            user=request.user,
            product=product,
            quantity=quantity,
            start_date=start,
            end_date=end,
            total_price=total_price,
        )

        return redirect('cart_view')

    return render(request, 'cart/add_to_cart.html', {'product': product})

@login_required(login_url='/accounts/login/')
def cart_view(request):
    items = CartItem.objects.filter(user=request.user, is_checked_out=False)
    total = sum(i.total_price for i in items)
    return render(request, 'cart/cart.html', {'items': items, 'total': total})
@login_required
def delete_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('cart_view')
@login_required
def checkout(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user, is_checked_out=False)

    if not cart_items.exists():
        return redirect("cart_view")

    total = sum(item.total_price for item in cart_items)
    # print(total)
    if request.method == "POST":
        address = request.POST.get("address")

        # 1) Create order
        order = Order.objects.create(
            user=user,
            total_amount=total,
            address=address,
        )

        # 2) Move cart items → order items
        for item in cart_items:
            OrderItem.objects.create(order=order, cart_item=item)
            item.is_checked_out = True
            item.save()

        # 3) Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(total * 100),
            "currency": "INR",
            "receipt": str(order.id),
            "payment_capture": 1
        })
        # print(int(total * 100))

        # 4) Create local Payment entry
        payment=Payment.objects.create(
            user=user,
            order=order,
            razorpay_order_id=razorpay_order["id"],
            amount=int(total * 100)
        )

        # 5) Send to payment page
        return render(request, "payments/payment_page.html", {
    "order": order,
    "total": total,
    "payment": payment,  # IMPORTANT!!!
    "razorpay_order_id": razorpay_order["id"],
    "razorpay_key": settings.RAZORPAY_KEY_ID,
})
    return render(request, "cart/checkout.html", {"total": total})
