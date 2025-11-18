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
    class Meta:
        model = RecipeIngredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class UserProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProduct
        fields = '__all__'


class GenerateRecipeSerializer(serializers.Serializer):
    """Serializer для запиту на генерацію рецепту через AI."""
    prompt = serializers.CharField(
        required=True,
        help_text="Опис бажаного рецепту (напр. 'паста з креветками')"
    )
    cuisine = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Тип кухні (напр. 'Italian', 'Chinese')"
    )
    complexity = serializers.ChoiceField(
        choices=['easy', 'medium', 'hard'],
        required=False,
        allow_blank=True,
        help_text="Складність приготування"
    )
    cooking_time = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Максимальний час приготування (хвилини)"
    )
    servings = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Кількість порцій"
    )
