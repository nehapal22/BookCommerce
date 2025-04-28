from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from store.models import Product
from cart.cart import Cart
from decimal import Decimal
from .models import ShippingAddress, Payment, Order, OrderItem
from .forms import paymentForm
from django.contrib import messages


@login_required
def payment_success(request):
    if request.method == 'POST':
        #get billing from last page
        payment_form = paymentForm(request.POST or None)
        #get shipping from last page
        my_shipping = request.session.get('my_shipping')
        print(my_shipping)
        messages.success(request, "Payment successful")
        return redirect('home')
    else:
        messages.error(request, "Payment denied")
        return redirect('payment:checkout')

@login_required
def process_order(request):
    if request.method == 'POST':
        cart = Cart(request)
        cart_items = cart.get_items()
        total = cart.cart_total()
        payment_form = paymentForm(request.POST or None)
        my_shipping = request.session.get('my_shipping')
        
        if not cart_items or not my_shipping:
            messages.error(request, "Cart is empty or shipping information is missing")
            return redirect('store:home')
            
        #gather user info
        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        #create shipping address from session info
        my_shipping = (
            f"{my_shipping['shipping_address1']}\n"
            f"{my_shipping['shipping_address2']}\n"
            f"{my_shipping['shipping_city']}\n"
            f"{my_shipping['shipping_state']}\n"
            f"{my_shipping['shipping_zip_code']}\n"
            f"{my_shipping['shipping_country']}"
        )
        
        # Add shipping cost to total
        shipping = Decimal('50.00')
        amount_paid = total + shipping
                        
        if request.user.is_authenticated:
            user = request.user
            # Create the order
            create_order = Order.objects.create(
                user=user,
                full_name=full_name,
                email=email,
                shipping_address=my_shipping,
                amount_paid=amount_paid
            )
            
            # Create order items
            for product in cart_items:
                product_id = product['product_id']
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price
                    
                create_order_item = OrderItem(
                    product_id=product_id,
                    quantity=product['quantity'],
                    user=user,
                    order=create_order,
                    price=price
                )
                create_order_item.save()
            
            order_id = create_order.pk
            
            # Clear the cart
            request.session['session_key'] = {}
            request.session.modified = True
            
            messages.success(request, "Order placed successfully!")
            return redirect('store:home')
        else:
             # Create order items
            for product in cart_items:
                product_id = product['product_id']
                if product.is_sale:
                    price = product.sale_price
                else:
                    price = product.price
                    
                create_order_item = OrderItem(
                    product_id=product_id,
                    quantity=product['quantity'],
                    order=create_order,
                    price=price
                )
                create_order_item.save()
            
            order_id = create_order.pk
            
            # Clear the cart
            request.session['session_key'] = {}
            request.session.modified = True
            messages.error(request, "User not authenticated")
            return redirect('store:home')
        
    else:
        messages.error(request, "Invalid request method")
        return redirect('payment:checkout')

@login_required
def billing_info(request):
    cart = Cart(request)
    cart_items = cart.get_items()
    total = cart.cart_total()
    #create session with shipiing info
    my_shipping = request.POST
    request.session['my_shipping'] = my_shipping
    
    if not cart_items:
        return redirect('store:home')
    
    # Calculate shipping cost
    shipping = Decimal('50.00')
    
    # Calculate grand total
    grand_total = total + shipping
    
    # Get user's saved addresses
    saved_addresses = ShippingAddress.objects.filter(user=request.user)
    
    # Initialize payment form
    payment_form = paymentForm()
        
    return render(request, 'payment/billing_info.html', {
        'cart_items': cart_items,
        'total': total,
        'shipping': shipping,
        'grand_total': grand_total,
        'saved_addresses': saved_addresses,
        'payment_form': payment_form
    })

@login_required
def process_billing_info(request):
    if request.method == 'POST':
        # Check if user selected a saved address
        address_choice = request.POST.get('address_choice')
        if address_choice and address_choice != 'new':
            saved_address = ShippingAddress.objects.get(id=address_choice)
            # Store billing information in session
            request.session['billing_info'] = {
                'billing_full_name': saved_address.shipping_full_name,
                'billing_email': request.user.email,
                'billing_address1': saved_address.shipping_address1,
                'billing_address2': saved_address.shipping_address2,
                'billing_city': saved_address.shipping_city,
                'billing_state': saved_address.shipping_state,
                'billing_zip_code': saved_address.shipping_zip_code,
                'billing_country': saved_address.shipping_country,
                'card_name': request.POST.get('card_name'),
                'card_number': request.POST.get('card_number'),
                'card_expiry': request.POST.get('card_expiry'),
                'card_cvv': request.POST.get('card_cvv')
            }
        else:
            # Store billing information in session
            request.session['billing_info'] = {
                'billing_full_name': request.POST.get('billing_full_name'),
                'billing_email': request.POST.get('billing_email'),
                'billing_address1': request.POST.get('billing_address1'),
                'billing_address2': request.POST.get('billing_address2'),
                'billing_city': request.POST.get('billing_city'),
                'billing_state': request.POST.get('billing_state'),
                'billing_zip_code': request.POST.get('billing_zip_code'),
                'billing_country': request.POST.get('billing_country'),
                'card_name': request.POST.get('card_name'),
                'card_number': request.POST.get('card_number'),
                'card_expiry': request.POST.get('card_expiry'),
                'card_cvv': request.POST.get('card_cvv')
            }
        return redirect('payment:checkout')
    return redirect('payment:billing_info')

@login_required
def checkout(request):
    cart = Cart(request)
    cart_items = cart.get_items()
    total = cart.cart_total()
    
    if not cart_items:
        return redirect('store:home')
        
    billing_info = request.session.get('billing_info')
    if not billing_info:
        return redirect('payment:billing_info')
    
    # Calculate shipping cost
    shipping = Decimal('50.00')
    
    # Calculate grand total
    grand_total = total + shipping
    
    # Prepare payment info for display
    payment_info = {
        'card_name': billing_info.get('card_name'),
        'card_number': billing_info.get('card_number'),
        'card_expiry': billing_info.get('card_expiry')
    }
        
    return render(request, 'payment/checkout.html', {
        'cart_items': cart_items,
        'total': total,
        'shipping': shipping,
        'grand_total': grand_total,
        'billing_info': billing_info,
        'payment_info': payment_info
    })

@login_required
def process_payment(request):
    if request.method == 'POST':
        cart = Cart(request)
        cart_items = cart.get_items()
        billing_info = request.session.get('billing_info')
        
        if not cart_items or not billing_info:
            return redirect('store:home')
            
        # Create the order
        user = request.user
        total = cart.cart_total()
        shipping = Decimal('50.00')
        grand_total = total + shipping
        
        # Create shipping address string
        shipping_address = (
            f"{billing_info['billing_address1']}\n"
            f"{billing_info['billing_address2']}\n"
            f"{billing_info['billing_city']}\n"
            f"{billing_info['billing_state']}\n"
            f"{billing_info['billing_zip_code']}\n"
            f"{billing_info['billing_country']}"
        )
        
        # Create the order
        create_order = Order.objects.create(
            user=user,
            full_name=billing_info['billing_full_name'],
            email=billing_info['billing_email'],
            shipping_address=shipping_address,
            amount_paid=grand_total
        )
        
        # Create order items and track purchases
        for item in cart_items:
            OrderItem.objects.create(
                product=item['product'],
                quantity=item['quantity'],
                user=user,
                order=create_order,
                price=item['price']
            )
            
            # Track purchase
            from recommender.views import track_interaction
            track_interaction(request, item['product'].id, 'purchase')
        
        # Clear the cart
        request.session['session_key'] = {}
        request.session.modified = True
        
        # Clear billing info from session
        if 'billing_info' in request.session:
            del request.session['billing_info']
        
        messages.success(request, "Order placed successfully!")
        return redirect('payment:success')
        
    return redirect('payment:checkout')

@login_required
def success(request):
    return render(request, 'payment/success.html')

@login_required
def shipped_dashboard(request):
    orders = Order.objects.filter(user=request.user, shipped=True).order_by('-date_ordered')
    return render(request, 'payment/shipped_dashboard.html', {
        'orders': orders,
        'title': 'Shipped Orders'
    })

@login_required
def not_shipped_dashboard(request):
    orders = Order.objects.filter(user=request.user, shipped=False).order_by('-date_ordered')
    return render(request, 'payment/not_shipped_dashboard.html', {
        'orders': orders,
        'title': 'Pending Orders'
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.orderitem_set.all()
    
    return render(request, 'payment/order_detail.html', {
        'order': order,
        'order_items': order_items,
        'title': f'Order #{order.id} Details'
    })
