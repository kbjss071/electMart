from django.shortcuts import render, redirect
from django.http import JsonResponse
from carts.models import CartItem
from .forms import OrderForm
from .models import Order, Payment, OrderProduct
from store.models import Product
import datetime
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

# Create your views here.
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number= body['orderID'])

    # Create a new Payment
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )

    payment.save()

    # Save the order
    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderProduct = OrderProduct()
        orderProduct.order_id = order.id
        orderProduct.payment = payment
        orderProduct.user_id = request.user.id
        orderProduct.product_id = item.product_id
        orderProduct.quantity = item.quantity
        orderProduct.product_price = item.product.price
        orderProduct.ordered = True
        orderProduct.save()
        
        itm = CartItem.objects.get(id=item.id)
        product_variation = itm.variation.all()
        orderProduct = OrderProduct.objects.get(id=orderProduct.id)
        orderProduct.variation.set(product_variation)
        orderProduct.save()


    # Reduce the quantity of the sold products
    product = Product.objects.get(id=item.product.id)
    product.stock -= item.quantity
    product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order receieved email to customer
    # mail_subject = 'Thank you for your order!'
    # message = render_to_string('orders/order_received_email.html', {
    #     'user': request.user,
    #     'order': order,
    # })
    # to_email = request.user.email
    # send_email = EmailMessage(mail_subject, message, to=[to_email])
    # send_email.send()

    # Send order number and transaction id back to handle response after payment
    data = {
        'order_number': order.order_number,
        'payment_id': payment.payment_id
    }

    return JsonResponse(data)

def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is equal to 0, then redirect user to store
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    
    grand_total=0
    tax = 0

    for item in cart_items:
        total += (item.product.price * item.quantity)
        quantity += item.quantity

    tax = (2 * total)/100
    grand_total = total + tax
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store the billing information
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # Generate order number which is equal to current_date + order.id
            year = int(datetime.date.today().strftime('%Y'))
            month = int(datetime.date.today().strftime('%m'))
            day = int(datetime.date.today().strftime('%d'))
            date = datetime.date(year, month, day)
            current_date = date.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order_id=order.id)

        payment = Payment.objects.get(payment_id=payment_id)

        subtotal = 0
        for i in order_products:
            subtotal += i.product_price * i.quantity

        context = {
            'order': order,
            'ordered_products': order_products,
            'order_number': order.order_number,
            'payment_id': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except(Payment.DoesNotExist, Order.DoesNotExist):
        # If the given url is wrong, send user back to home.
        return redirect('home')
        