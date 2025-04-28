import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.db.models import Count, Avg
from .models import UserProductInteraction, ProductSimilarity
from store.models import Product
from django.contrib.auth.models import User

class Recommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def get_user_interactions(self, user):
        """Get all interactions for a user"""
        return UserProductInteraction.objects.filter(user=user)
    
    def get_product_features(self, product):
        """Extract features from product for content-based filtering"""
        features = [
            product.name,
            product.description or '',
            product.category.name
        ]
        return ' '.join(features)
    
    def update_product_similarities(self):
        """Update similarity scores between products"""
        products = Product.objects.all()
        features = [self.get_product_features(p) for p in products]
        
        # Create TF-IDF matrix
        tfidf_matrix = self.vectorizer.fit_transform(features)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Update similarity scores in database
        for i, product in enumerate(products):
            for j, similar_product in enumerate(products):
                if i != j:
                    ProductSimilarity.objects.update_or_create(
                        product=product,
                        similar_product=similar_product,
                        defaults={'similarity_score': similarity_matrix[i][j]}
                    )
    
    def get_content_based_recommendations(self, product, n=5):
        """Get content-based recommendations for a product"""
        similarities = ProductSimilarity.objects.filter(
            product=product
        ).order_by('-similarity_score')[:n]
        return [s.similar_product for s in similarities]
    
    def get_collaborative_recommendations(self, user, n=5):
        """Get collaborative filtering recommendations for a user"""
        # Get all user interactions
        interactions = self.get_user_interactions(user)
        
        # Get products the user hasn't interacted with
        user_products = set(interactions.values_list('product', flat=True))
        all_products = set(Product.objects.values_list('id', flat=True))
        candidate_products = all_products - user_products
        
        # Calculate average interaction scores for each product
        product_scores = {}
        for product_id in candidate_products:
            product_interactions = UserProductInteraction.objects.filter(
                product_id=product_id
            ).aggregate(
                avg_score=Avg('weight')
            )
            product_scores[product_id] = product_interactions['avg_score'] or 0
        
        # Get top N products
        recommended_product_ids = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]
        
        return Product.objects.filter(id__in=[p[0] for p in recommended_product_ids])
    
    def get_hybrid_recommendations(self, user, n=5):
        """Get hybrid recommendations combining both methods"""
        # Get collaborative recommendations
        collab_recs = self.get_collaborative_recommendations(user, n)
        
        # Get content-based recommendations for each collaborative recommendation
        hybrid_recs = []
        for product in collab_recs:
            content_recs = self.get_content_based_recommendations(product, 1)
            if content_recs:
                hybrid_recs.extend(content_recs)
        
        # Remove duplicates and limit to n recommendations
        seen = set()
        unique_recs = []
        for rec in hybrid_recs:
            if rec.id not in seen:
                seen.add(rec.id)
                unique_recs.append(rec)
                if len(unique_recs) == n:
                    break
        
        return unique_recs 