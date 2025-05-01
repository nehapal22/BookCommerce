from django.contrib import admin
from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path("", views.home, name= 'home'),
    path("about/", views.about, name= 'about'),
    path("login/", views.login_user, name= 'login'),
    path("logout/", views.logout_user, name= 'logout'),
    path("register/", views.register_user, name= 'register'),
    path("update_password/", views.update_password, name= 'update_password'),

    path("update_user/", views.update_user, name= 'update_user'),
    path("update_info/", views.update_info, name= 'update_info'),
    path("product/<int:pk>", views.product, name= 'product'),
    path("category/<slug:category_slug>/", views.category_view, name='category'),
    path("category_summary/", views.category_summary, name='category_summary'),
    path("search/", views.search, name= 'search'),

    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:review_id>/delete/', views.delete_review, name='delete_review'),
]
