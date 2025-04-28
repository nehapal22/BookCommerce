from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Profile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm
from payment.models import ShippingAddress
from payment.forms import ShippingForm
from django import forms
from django.http import JsonResponse, Http404
import logging
from cart.cart import Cart
from django.db import models
import json
from recommender.recommender import Recommender

logger = logging.getLogger(__name__)

def get_categories():
    """Helper function to get all parent categories"""
    return Category.objects.filter(parent=None)

def product(request, pk):
    try:
        product = get_object_or_404(Product, id=pk)
        
        # Track product view if user is logged in
        if request.user.is_authenticated:
            from recommender.views import track_interaction
            track_interaction(request, pk, 'view')
        
        # Get recommendations for this product
        recommender = Recommender()
        recommendations = recommender.get_content_based_recommendations(product, n=4)
        
        return render(request, 'product.html', {
            'product': product,
            'categories': get_categories(),
            'recommendations': recommendations
        })
    except Http404:
        messages.error(request, 'Product not found')
        return redirect('home')

def home(request):
    products = Product.objects.all()
    
    # Get personalized recommendations if user is logged in
    recommendations = None
    if request.user.is_authenticated:
        recommender = Recommender()
        recommendations = recommender.get_hybrid_recommendations(request.user, n=4)
    
    return render(request, 'home.html', {
        'products': products,
        'categories': get_categories(),
        'recommendations': recommendations
    })

def category_view(request, category_slug):
    try:
        category = get_object_or_404(Category, slug=category_slug)
        subcategories = category.get_subcategories()
        products = category.get_products()
        
        return render(request, 'category.html', {
            'category': category,
            'subcategories': subcategories,
            'products': products,
            'categories': get_categories()
        })
    except Http404:
        messages.error(request, 'Category not found')
        return redirect('category_summary')

def category_summary(request):
    return render(request, 'category_summary.html', {
        'categories': get_categories()
    })

def about(request):
    return render(request, 'about.html', {
        'categories': get_categories()
    })

def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Do some shopping cart stuff
            try:
                current_user = Profile.objects.get(user__id=request.user.id)
                # Get their saved cart from database
                saved_cart = current_user.old_cart
                # Convert database string to python dictionary
                if saved_cart and saved_cart.strip():
                    try:
                        # Convert to dictionary using JSON
                        converted_cart = json.loads(saved_cart)
                        # Get the cart
                        cart = Cart(request)
                        # Loop thru the cart and add the items from the database
                        for key, value in converted_cart.items():
                            try:
                                product = Product.objects.get(id=key)
                                cart.db_add(product=product, quantity=value)
                            except Product.DoesNotExist:
                                continue
                        messages.success(request, "Your cart has been restored!")
                    except json.JSONDecodeError:
                        messages.warning(request, "Could not restore your cart. Starting with an empty cart.")
            except Profile.DoesNotExist:
                messages.warning(request, "No profile found. Starting with an empty cart.")

            messages.success(request, "You Have Been Logged In!")
            return redirect('store:home')
        else:
            messages.success(request, "There was an error, please try again...")
            return redirect('store:login')
    else:
        return render(request, 'login.html', {})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out...")
    return redirect('store:home')

def register_user(request):
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in')
        return redirect('home')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created successfully.')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SignUpForm()
        
    return render(request, 'register.html', {
        'form': form,
        'categories': get_categories()
    })

@login_required
def update_user(request):
    if request.user.is_authenticated:
        current_user = Profile.objects.get(user_id=request.user.id)
        shipping_user = ShippingAddress.objects.get(user_id=request.user.id)
        
        if request.method == 'POST':
            user_form = UpdateUserForm(request.POST, instance=request.user)
            shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
            
            if user_form.is_valid() and shipping_form.is_valid():
                user_form.save()
                shipping_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('home')
            else:
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
        else:
            user_form = UpdateUserForm(instance=request.user)
    
        return render(request, "update_user.html", {
            'user_form': user_form,
            'categories': get_categories()
        })

@login_required
def update_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ChangePasswordForm(request.user)
    
    return render(request, 'update_password.html', {
        'form': form,
        'categories': get_categories()
    })

@login_required
def update_info(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()
        
    try:
        shipping_address = ShippingAddress.objects.get(user=request.user)
    except ShippingAddress.DoesNotExist:
        shipping_address = None
        
    if request.method == 'POST':
        form = UserInfoForm(request.POST, instance=profile)
        shipping_form = ShippingForm(request.POST, instance=shipping_address)
        
        if form.is_valid() and shipping_form.is_valid():
            form.save()
            shipping = shipping_form.save(commit=False)
            shipping.user = request.user
            shipping.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('store:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserInfoForm(instance=profile)
        shipping_form = ShippingForm(instance=shipping_address)
        
    return render(request, 'update_info.html', {
        'form': form,
        'categories': get_categories(),
        'shipping_form': shipping_form
    })

@login_required
def update_address(request):
    pass

def update_payment(request):
    pass

def search(request):
    if request.method == 'POST':
        searched = request.POST.get('searched', '')
        # Search in both name and description by query
        products = Product.objects.filter(
            models.Q(name__icontains=searched) | 
            models.Q(description__icontains=searched)
        )
        return render(request, "search.html", {
            'searched': searched,
            'products': products,
            'categories': get_categories()
        })
    else:
        return render(request, "search.html", {
            'categories': get_categories()
        })