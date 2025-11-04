from django.contrib import admin
from .models import (
    Recipe, MeasurementUnit, Category, Cuisine, 
    Complexity, Ingredient, UserProduct, RecipeIngredient
)

admin.site.register(Recipe)
admin.site.register(MeasurementUnit)
admin.site.register(Category)
admin.site.register(Cuisine)
admin.site.register(Complexity)
admin.site.register(Ingredient)
admin.site.register(UserProduct)
admin.site.register(RecipeIngredient)
