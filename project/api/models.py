from django.db import models

class MeasurementUnit(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Cuisine(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Complexity(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.ForeignKey(MeasurementUnit, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    cooking_time = models.PositiveIntegerField(null=True, blank=True)
    servings = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    rating = models.FloatField(default=0.0)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    cuisine = models.ForeignKey(Cuisine, on_delete=models.SET_NULL, null=True, blank=True)
    complexity = models.ForeignKey(Complexity, on_delete=models.SET_NULL, null=True, blank=True)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
