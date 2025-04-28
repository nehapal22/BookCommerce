import json
from store.models import Product, Profile

class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        # Get the current cart from the session
        cart = self.session.get('session_key')
        # If the user is new, no session key! Create one!
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
        self.cart = cart
     
    def db_add(self, product, quantity):
        product_id = str(product.id)
        product_qty = int(quantity)
        
        # Logic
        if product_id in self.cart:
            pass
        else:
            self.cart[product_id] = product_qty
            
        self.session.modified = True
        self.save_cart_to_profile()
            
    def add(self, product):
        product_id = str(product.id)
        
        # Logic
        if product_id in self.cart:
            pass
        else:
            self.cart[product_id] = 1
         
        self.session.modified = True
        self.save_cart_to_profile()
                
    def save_cart_to_profile(self):
        """Save cart data to user's profile"""
        if self.request.user.is_authenticated:
            try:
                current_user = Profile.objects.get(user__id=self.request.user.id)
                # Convert cart to JSON string
                cart_data = json.dumps(self.cart)
                current_user.old_cart = cart_data
                current_user.save()
            except Profile.DoesNotExist:
                pass
                
    def update(self, product_id, quantity):
        """
        Update quantity of a product in cart
        """
        product_id = str(product_id)
        product_qty = int(quantity)
        
        # Get cart
        ourcart = self.cart
        # Update Dictionary/cart
        ourcart[product_id] = product_qty
        
        self.session.modified = True
        self.save_cart_to_profile()
        
    def delete(self, product_id):
        """
        Delete item from cart
        """
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.session.modified = True
            self.save_cart_to_profile()
        
    def __len__(self):
        return len(self.cart)
    
    def get_prods(self):
        # Get ids from cart
        product_ids = self.cart.keys()
        # Use ids to lookup products in database model
        products = Product.objects.filter(id__in=product_ids)
        return products
    
    def get_quants(self):
        quantities = self.cart
        return quantities
    
    def cart_total(self):
        # Get product IDs
        product_ids = self.cart.keys()
        # lookup those keys in our products database model
        products = Product.objects.filter(id__in=product_ids)
        # Get quantities
        quantities = self.cart
        # Start counting at 0
        total = 0
        
        for key, value in quantities.items():
            # Convert key string into int so we can do math
            key = int(key)
            for product in products:
                if product.id == key:
                    if product.is_sale:
                        total = total + (product.sale_price * value)
                    else:
                        total = total + (product.price * value)
        
        return total
    
    def get_items(self):
        items = []
        for product_id, quantity in self.cart.items():
            try:
                product = Product.objects.get(id=product_id)
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'price': float(product.sale_price if product.is_sale else product.price),
                    'original_price': float(product.price),
                    'is_sale': product.is_sale,
                    'total': (product.sale_price if product.is_sale else product.price) * quantity
                })
            except Product.DoesNotExist:
                continue
        return items