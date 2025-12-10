import razorpay
from django.conf import settings
from django.shortcuts import redirect
from cart.models import Order
from .models import Payment
from django.http import HttpResponse

def verify_payment(request):
    order_id = request.GET.get("order")
    payment_id = request.GET.get("payment_id")
    signature = request.GET.get("signature")
    print(order_id, payment_id, signature)
    order = Order.objects.get(id=order_id)
    payment = Payment.objects.get(order=order)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_SECRET))

    data = {
        "razorpay_order_id": payment.razorpay_order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature
    }

    try:
        client.utility.verify_payment_signature(data)

        # Success
        payment.status = "SUCCESS"
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.save()

        # return redirect("order_success", order.id)
        return HttpResponse("Payment Successful")

    except:
        payment.status = "FAILED"
        payment.save()
        return redirect("cart_view")
    
    
