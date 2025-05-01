from django.contrib import admin
from .models import Category, Customer, Product, Order, OrderItem, BookReview, Profile
from django.utils.text import slugify
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    list_filter = ('parent',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Profile)

class ProfileInine(admin.StackedInline):
    model = Profile

class UserAdmin(BaseUserAdmin):
    model = User
    field = ["username", "email", "password", "is_staff"]
    list_display = ["username", "email", "is_staff"]
    list_filter = ["is_staff"]
    inlines = [ProfileInine]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__name', 'user__username', 'content')