from api.models import (
    MeasurementUnit, Category, Cuisine, Complexity,
    Ingredient, Recipe, RecipeIngredient, UserProduct
    )
from rest_framework import serializers


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class CuisineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cuisine
        fields = '__all__'


class ComplexitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Complexity
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    unit = MeasurementUnitSerializer(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    cuisine = CuisineSerializer(read_only=True)
    complexity = ComplexitySerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class UserProductSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient', write_only=True
    )
    class Meta:
        model = UserProduct
        fields = '__all__'


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    recipe = RecipeSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(), source='recipe', write_only=True
    )

    class Meta:
        model = FavoriteRecipe
        fields = 'all'
        read_only_fields = ['user', 'created_at']