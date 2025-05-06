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
    # Check if there's an order in the session
    billing_info = request.session.get('billing_info')
    if billing_info:
        messages.success(request, "Payment successful")
        # Clear billing info from session
        if 'billing_info' in request.session:
            del request.session['billing_info']
        return redirect('store:home')
    else:
        messages.error(request, "No order information found")
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
        print("Received POST request to process_billing_info")
        print("POST data:", request.POST)
        
        # Get payment method
        payment_method = request.POST.get('payment_method', 'card')
        print("Selected payment method:", payment_method)
        
        # Check if user selected a saved address
        address_choice = request.POST.get('address_choice')
        print("Address choice:", address_choice)
        
        try:
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
                    'payment_method': payment_method
                }
                
                if payment_method == 'card':
                    request.session['billing_info'].update({
                        'card_name': request.POST.get('card_name'),
                        'card_number': request.POST.get('card_number'),
                        'card_expiry': request.POST.get('card_expiry'),
                        'card_cvv': request.POST.get('card_cvv')
                    })
            else:
                # Validate required fields
                required_fields = ['billing_full_name', 'billing_email', 'billing_address1', 
                                 'billing_city', 'billing_country']
                
                missing_fields = [field for field in required_fields 
                                if not request.POST.get(field)]
                
                if missing_fields:
                    print("Missing required fields:", missing_fields)
                    messages.error(request, f"Please fill in all required fields: {', '.join(missing_fields)}")
                    return redirect('payment:billing_info')
                
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
                    'payment_method': payment_method
                }
                
                if payment_method == 'card':
                    # Validate card fields
                    card_fields = ['card_name', 'card_number', 'card_expiry', 'card_cvv']
                    missing_card_fields = [field for field in card_fields 
                                        if not request.POST.get(field)]
                    
                    if missing_card_fields:
                        print("Missing card fields:", missing_card_fields)
                        messages.error(request, f"Please fill in all card details: {', '.join(missing_card_fields)}")
                        return redirect('payment:billing_info')
                    
                    request.session['billing_info'].update({
                        'card_name': request.POST.get('card_name'),
                        'card_number': request.POST.get('card_number'),
                        'card_expiry': request.POST.get('card_expiry'),
                        'card_cvv': request.POST.get('card_cvv')
                    })
            
            print("Successfully stored billing info in session")
            return redirect('payment:checkout')
            
        except Exception as e:
            print("Error processing billing info:", str(e))
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('payment:billing_info')
    
    print("Non-POST request to process_billing_info")
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
        if not cart.cart:
            messages.error(request, "Your cart is empty")
            return redirect('store:home')
        
        billing_info = request.session.get('billing_info')
        if not billing_info:
            messages.error(request, "Billing information is missing")
            return redirect('payment:billing_info')
        
        # Calculate total amount
        total_amount = Decimal('0.00')
        for product_id, quantity in cart.cart.items():
            product = get_object_or_404(Product, id=product_id)
            total_amount += product.price * Decimal(str(quantity))
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=billing_info['billing_full_name'],
            email=billing_info['billing_email'],
            shipping_address=f"{billing_info['billing_address1']}\n{billing_info.get('billing_address2', '')}\n{billing_info['billing_city']}, {billing_info['billing_state']} {billing_info['billing_zip_code']}\n{billing_info['billing_country']}",
            amount_paid=total_amount
        )
        
        # Create order items
        for product_id, quantity in cart.cart.items():
            product = get_object_or_404(Product, id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )
        
        # Save payment information if it's a card payment
        if billing_info.get('payment_method') == 'card':
            Payment.objects.create(
                user=request.user,
                order=order,
                payment_method='card',
                card_name=billing_info['card_name'],
                card_number=billing_info['card_number'],
                card_expiry=billing_info['card_expiry'],
                card_cvv=billing_info['card_cvv']
            )
        else:
            Payment.objects.create(
                user=request.user,
                order=order,
                payment_method='cod'
            )
        
        # Clear the cart and billing info
        cart.clear()
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
