from django.shortcuts import render, get_object_or_404, redirect
from .cart import Cart
from store.models import Product
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from recommender.views import track_interaction

def cart_summary(request):
	# Get the cart
	cart = Cart(request)
	cart_items = cart.get_items()
	total = cart.cart_total()
	return render(request, "cart_summary.html", {
		"cart_items": cart_items,
		"total": total
	})

@login_required
def cart_add(request):
	cart = Cart(request)
	
	if request.method == 'POST':
		product_id = int(request.POST.get('product_id'))
		product = get_object_or_404(Product, id=product_id)
		
		# Add to cart
		cart.add(product=product)
		
		# Track cart addition
		track_interaction(request, product_id, 'cart')
		
		# Get cart quantity
		cart_quantity = cart.__len__()
		
		# Return JSON response for AJAX
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({
				'success': True,
				'qty': cart_quantity,
				'cart_items_count': cart_quantity
			})
		
		messages.success(request, "Product Added To Cart...")
		return redirect("cart:cart_summary")
	
	return redirect("store:home")

@login_required
def item_clear(request, id):
	cart = Cart(request)
	product = Product.objects.get(id=id)
	cart.remove(product)
	return redirect("cart:cart_detail")

@login_required
def item_increment(request, id):
	cart = Cart(request)
	product = Product.objects.get(id=id)
	cart.add(product=product)
	return redirect("cart:cart_detail")

@login_required
def item_decrement(request, id):
	cart = Cart(request)
	product = Product.objects.get(id=id)
	cart.decrement(product=product)
	return redirect("cart:cart_detail")

@login_required
def cart_clear(request):
	cart = Cart(request)
	cart.clear()
	return redirect("cart:cart_detail")

@login_required
def cart_detail(request):
	cart = Cart(request)
	cart_items = cart.get_items()
	total = cart.cart_total()
	
	return render(request, 'cart/cart_detail.html', {
		'cart_items': cart_items,
		'total': total
	})

@login_required
def cart_delete(request):
	cart = Cart(request)
	if request.method == 'POST':
		product_id = int(request.POST.get('product_id'))
		cart.delete(product_id=product_id)
		
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			return JsonResponse({'success': True})
		
		messages.success(request, "Item Deleted From Shopping Cart...")
	return redirect("cart:cart_summary")

@login_required
def cart_update(request):
	cart = Cart(request)
	if request.method == 'POST':
		product_id = int(request.POST.get('product_id'))
		product_qty = int(request.POST.get('product_qty'))
		
		cart.update(product_id=product_id, quantity=product_qty)
		
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
			cart_items = cart.get_items()
			total = cart.cart_total()
			return JsonResponse({
				'success': True,
				'qty': product_qty,
				'total': total
			})
	
	return redirect("cart:cart_summary")
