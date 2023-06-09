from .models import Cart, CartItem
from .views import get_cart_id

def counter(request):
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=get_cart_id(request))
            # if user is authenticated, find cartItems on the requesting user
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                # returns cart_items under only one cart id.
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            cart_count = 0
            for item in cart_items:
                cart_count += item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)