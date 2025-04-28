from django.db import models
from django.contrib.auth.models import User
from store.models import Product
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
# Create your models here.

class ShippingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shipping_full_name = models.CharField(max_length=255)
    shipping_email = models.EmailField(max_length=255)
    shipping_address1 = models.CharField(max_length=500)
    shipping_address2 = models.CharField(max_length=500, null=True, blank=True)
    shipping_city = models.CharField(max_length=255, default='')
    shipping_state = models.CharField(max_length=255, null=True, blank=True)
    shipping_zip_code = models.CharField(max_length=255, null=True, blank=True)
    shipping_country = models.CharField(max_length=255)
    
    class Meta:
        
        verbose_name_plural = "Shipping Address"
        
    def __str__(self):
        return f"{self.shipping_full_name} - {self.shipping_address1} - {self.shipping_city} - {self.shipping_state} - {self.shipping_zip_code}"
    
 #order  model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    shipping_address = models.TextField(max_length=255)
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2)
    date_ordered = models.DateTimeField(auto_now_add=True)
    shipped = models.BooleanField(default=False)
    date_shipped = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f'Order - {str(self.id)}'
    
#auto add shipping dae
@receiver(pre_save, sender=Order)
def set_shipped_date_on_update(sender, instance, **kwargs):
    if instance.pk:
        now = datetime.datetime.now()
        obj = sender._default_manager.get(pk=instance.pk)
        if instance.shipped and not obj.shipped:
            instance.date_shipped = now
            
        
 #order.items.model
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name='payment_order_items')
    quantity = models.PositiveBigIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Order Item - {str(self.id)}'
        
    @property
    def get_total(self):
        return (self.price * self.quantity)
        
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card_name = models.CharField(max_length=100)
    card_number = models.CharField(max_length=16)
    card_expiry = models.CharField(max_length=5)
    card_cvv = models.CharField(max_length=3)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.card_name} - {self.card_number[-4:]}"
        
