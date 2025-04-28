from django.contrib import admin
from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('billing-info/', views.billing_info, name='billing_info'),
    path('process-billing-info/', views.process_billing_info, name='process_billing_info'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('success/', views.payment_success, name='success'),
    path('process_order/', views.process_order, name='process_order'),
    path('shipped_dashboard/', views.shipped_dashboard, name='shipped_dashboard'),
    path('not_shipped_dashboard/', views.not_shipped_dashboard, name='not_shipped_dashboard'),

    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
]
