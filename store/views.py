from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Profile, BookReview, ReviewComment
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm, UpdateUserForm, ChangePasswordForm, UserInfoForm, BookReviewForm
from payment.models import ShippingAddress, OrderItem
from payment.forms import ShippingForm
from django import forms
from django.http import JsonResponse, Http404
import logging
from cart.cart import Cart
from django.db import models, transaction
import json
from recommender.recommender import Recommender
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.db.models import Avg, Q
from django.urls import reverse

logger = logging.getLogger(__name__)

def get_categories():
    """Helper function to get all parent categories"""
    return Category.objects.filter(parent=None)

def product(request, pk):
    try:
        product = get_object_or_404(Product, id=pk)
        
        # Get reviews and average rating
        reviews = BookReview.objects.filter(book=product).select_related('user').prefetch_related('comments__user').order_by('-created_at')
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        
        # Check if user has already reviewed
        user_review = None
        if request.user.is_authenticated:
            user_review = BookReview.objects.filter(book=product, user=request.user).first()
            
            # Track product view
            from recommender.views import track_interaction
            track_interaction(request, pk, 'view')
        
        # Get recommendations for this product
        recommender = Recommender()
        recommendations = recommender.get_content_based_recommendations(product, n=4)
        
        context = {
            'product': product,
            'categories': get_categories(),
            'recommendations': recommendations,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'user_review': user_review,
            'reading_status_choices': BookReview.READING_STATUS_CHOICES,
        }
        return render(request, 'product.html', context)
    except Exception as e:
        logger.error(f"Error in product view: {str(e)}")
        messages.error(request, "Error loading product details")
        return redirect('store:home')

def home(request):
    products = Product.objects.all()
    show = request.GET.get('show', '')
    
    if show == 'my_reviews' and request.user.is_authenticated:
        # Get user's reviews
        reviews = BookReview.objects.filter(user=request.user).select_related('book', 'user').order_by('-created_at')
        return render(request, 'store/my_reviews.html', {
            'reviews': reviews,
            'categories': get_categories()
        })
    elif show == 'all_reviews':
        # Get all reviews
        reviews = BookReview.objects.all().select_related('book', 'user').order_by('-created_at')
        return render(request, 'store/all_reviews.html', {
            'reviews': reviews,
            'categories': get_categories()
        })
    
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
        return redirect('store:category_summary')

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

from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token

@csrf_protect
def register_user(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            
            # Authenticate and login the user
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Registration successful! Please complete your profile.")
                return redirect('store:update_info')
            else:
                messages.error(request, "Authentication failed after registration.")
        else:
            # Render the same page with form errors
            return render(request, 'register.html', {
                'form': form,
                'categories': get_categories()
            })
    
    # GET request or failed POST
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
                return redirect('store:home')
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
            return redirect('store:home')
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

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Check if user already reviewed this product
            existing_review = BookReview.objects.filter(book=product, user=request.user).first()
            if existing_review:
                messages.error(request, "You have already reviewed this product")
                return redirect('store:product', pk=product_id)
            
            # Get form data
            content = request.POST.get('content')
            reading_status = request.POST.get('reading_status', 'read')
            rating = request.POST.get('rating')
            
            # Validate content
            if not content:
                messages.error(request, "Review content is required")
                return redirect('store:product', pk=product_id)
            
            # Handle rating based on reading status
            if reading_status == 'want_to_read':
                rating = 0  # Set rating to 0 for want_to_read
            else:
                try:
                    rating = int(rating)
                    if not (1 <= rating <= 5):
                        messages.error(request, "Rating must be between 1 and 5")
                        return redirect('store:product', pk=product_id)
                except (TypeError, ValueError):
                    messages.error(request, "Valid rating is required for this reading status")
                    return redirect('store:product', pk=product_id)
            
            # Create review
            review = BookReview.objects.create(
                book=product,
                user=request.user,
                rating=rating,
                content=content,
                reading_status=reading_status
            )
            
            messages.success(request, "Review added successfully!")
            
        except Exception as e:
            logger.error(f"Error adding review: {str(e)}")
            messages.error(request, f"Error adding review: {str(e)}")
            
    return redirect('store:product', pk=product_id)

@login_required
def edit_review(request, review_id):
    review = get_object_or_404(BookReview, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = BookReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated successfully!")
            return redirect('store:product_detail', product_id=review.book.id)
    else:
        form = BookReviewForm(instance=review)
    
    return render(request, 'store/edit_review.html', {'form': form, 'review': review})

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(BookReview, id=review_id, user=request.user)
    product_id = review.book.id
    review.delete()
    messages.success(request, "Your review has been deleted successfully!")
    return redirect('store:product_detail', product_id=product_id)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().select_related('user').order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    
    # Check if user has already reviewed this product
    user_review = None
    if request.user.is_authenticated:
        user_review = BookReview.objects.filter(book=product, user=request.user).first()
    
    context = {
        'product': product,
        'reviews': reviews,
        'user_review': user_review,
        'avg_rating': avg_rating,
        'categories': get_categories()
    }
    return render(request, 'store/product_detail.html', context)

@login_required
def add_comment(request, review_id):
    review = get_object_or_404(BookReview, id=review_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = ReviewComment.objects.create(
                review=review,
                user=request.user,
                content=content
            )
            messages.success(request, "Comment added successfully!")
            return redirect('store:product', pk=review.book.id)
        else:
            messages.error(request, "Comment cannot be empty")
    return redirect('store:product', pk=review.book.id)

@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(ReviewComment, id=comment_id)
    if request.user != comment.user:
        messages.error(request, "You can only edit your own comments")
        return redirect('store:product', pk=comment.review.book.id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment.content = content
            comment.save()
            messages.success(request, "Comment updated successfully!")
        else:
            messages.error(request, "Comment cannot be empty")
    return redirect('store:product', pk=comment.review.book.id)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(ReviewComment, id=comment_id)
    if request.user != comment.user:
        messages.error(request, "You can only delete your own comments")
        return redirect('store:product', pk=comment.review.book.id)
    
    comment.delete()
    messages.success(request, "Comment deleted successfully!")
    return redirect('store:product', pk=comment.review.book.id)