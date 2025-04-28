from django.db import models
from store.models import Product, User
from django.db.models import Avg

# Create your models here.

class UserProductInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('cart', 'Add to Cart'),
        ('purchase', 'Purchase')
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    weight = models.FloatField(default=1.0)  # Weight for different interaction types

    class Meta:
        unique_together = ('user', 'product', 'interaction_type')

class ProductSimilarity(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='base_product')
    similar_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='similar_product')
    similarity_score = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'similar_product')
