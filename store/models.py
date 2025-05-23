from django.db import models
import datetime
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator, MaxValueValidator

#create customer profile
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_modified = models.DateTimeField(auto_now=True)
    phone = models.CharField(max_length=20, blank=True)
    address1 = models.CharField(max_length=250, blank=True)
    address2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    old_cart = models.CharField(max_length=5000, blank=True, null=True)
    
    def __str__(self):
        return self.user.username

#create default user profile
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()

#automate the profile thingy
post_save.connect(create_profile, sender=User) 

       
       
class Category(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    slug = models.SlugField(unique=True, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def get_subcategories(self):
        return self.subcategories.all()

    def get_products(self):
        return Product.objects.filter(category=self)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    
    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(max_length=250, default='', blank=True, null=True)
    image = models.ImageField(upload_to='uploads/product/')
    #add sale options
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=8)
    
    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f'Order {self.id} - {self.customer}'

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

class ShippingAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store_shipping_address')
    address1 = models.CharField(max_length=250, blank=True)
    address2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s shipping address"

class BookReview(models.Model):
    READING_STATUS_CHOICES = [
        ('read', 'Read'),
        ('want_to_read', 'Want to Read'),
        ('currently_reading', 'Currently Reading'),
        ('dnf', 'Did Not Finish')
    ]
    
    book = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Your Review", help_text="Share your thoughts about the book's content")
    rating = models.PositiveSmallIntegerField(
            validators=[MinValueValidator(1), MaxValueValidator(5)],
            help_text="Rating from 1 (poor) to 5 (excellent)"
        )
    reading_status = models.CharField(
        max_length=20,
        choices=READING_STATUS_CHOICES,
        default='read',
        verbose_name="Reading Status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['book', 'user']
    
    def __str__(self):
        return f"{self.user.username}'s review of {self.book.name}"

class ReviewComment(models.Model):
    review = models.ForeignKey(BookReview, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Your Comment", help_text="Share your thoughts about this review")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.review.user.username}'s review"