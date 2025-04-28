from django.urls import path
from . import views

app_name = 'recommender'

urlpatterns = [
    path('track/<int:product_id>/<str:interaction_type>/', views.track_interaction, name='track_interaction'),
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
] 