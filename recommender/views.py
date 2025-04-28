from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .recommender import Recommender
from .models import UserProductInteraction
from store.models import Product
from django.http import JsonResponse
from django.db import transaction

# Create your views here.

@login_required
def track_interaction(request, product_id, interaction_type):
    """Track user interactions with products"""
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            weight = {
                'view': 1.0,
                'cart': 2.0,
                'purchase': 3.0
            }.get(interaction_type, 1.0)
            
            # Use update_or_create to handle duplicate interactions
            with transaction.atomic():
                interaction, created = UserProductInteraction.objects.update_or_create(
                    user=request.user,
                    product=product,
                    interaction_type=interaction_type,
                    defaults={'weight': weight}
                )
            
            return JsonResponse({'status': 'success'})
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def get_recommendations(request):
    """Get recommendations for the current user"""
    recommender = Recommender()
    recommendations = recommender.get_hybrid_recommendations(request.user, n=5)
    
    return render(request, 'recommender/recommendations.html', {
        'recommendations': recommendations
    })
