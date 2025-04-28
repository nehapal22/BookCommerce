from .models import Category

def categories_context(request):
    """Context processor to make categories available in all templates"""
    return {
        'categories': Category.objects.filter(parent=None)
    } 