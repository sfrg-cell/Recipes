from api.models import (
    Recipe, MeasurementUnit, Category, Cuisine,
    Complexity, Ingredient, UserProduct
)
from api.serializers import (
    RecipeSerializer, MeasurementUnitSerializer, CategorySerializer,
    CuisineSerializer, ComplexitySerializer, IngredientSerializer,
    UserProductSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import Http404
from rest_framework import status
from .filters import RecipeFilter
import random
from django.db.models import Max


class RecipeList(APIView):
    def get(self, request, format=None):
        recipes = Recipe.objects.all()
        recipe_filter = RecipeFilter(request.GET, queryset=recipes)
        filtered_recipes = recipe_filter.qs
        serializer = RecipeSerializer(filtered_recipes, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeDetail(APIView):
    def get_object(self, pk):
        try:
            return Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        recipe = self.get_object(pk)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        recipe = self.get_object(pk)
        serializer = RecipeSerializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        recipe = self.get_object(pk)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RandomRecipe(APIView):
    def get(self, request, format=None):
        max_id = Recipe.objects.aggregate(max_id=Max("id"))['max_id']
        
        if max_id is None:
            return Response({'error': 'No recipes found'}, status=status.HTTP_404_NOT_FOUND)
        
        for _ in range(10):
            random_id = random.randint(1, max_id)
            random_recipe = Recipe.objects.filter(id=random_id).first()
            if random_recipe:
                serializer = RecipeSerializer(random_recipe)
                return Response(serializer.data)
        
        fallback_recipe = Recipe.objects.first()
        if fallback_recipe:
            serializer = RecipeSerializer(fallback_recipe)
            return Response(serializer.data)
        
        return Response({'error': 'No recipes found'}, status=status.HTTP_404_NOT_FOUND)
   

class MeasurementUnitList(APIView):
    def get(self, request, format=None):
        units = MeasurementUnit.objects.all()
        serializer = MeasurementUnitSerializer(units, many=True)
        return Response(serializer.data)


class CategoryList(APIView):
    def get(self, request, format=None):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CuisineList(APIView):
    def get(self, request, format=None):
        cuisines = Cuisine.objects.all()
        serializer = CuisineSerializer(cuisines, many=True)
        return Response(serializer.data)


class ComplexityList(APIView):
    def get(self, request, format=None):
        complexities = Complexity.objects.all()
        serializer = ComplexitySerializer(complexities, many=True)
        return Response(serializer.data)


class IngredientList(APIView):
    def get(self, request, format=None):
        ingredients = Ingredient.objects.all()
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = IngredientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IngredientDetail(APIView):
    def get_object(self, pk):
        try:
            return Ingredient.objects.get(pk=pk)
        except Ingredient.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        ingredient = self.get_object(pk)
        serializer = IngredientSerializer(ingredient)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        ingredient = self.get_object(pk)
        serializer = IngredientSerializer(ingredient, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        ingredient = self.get_object(pk)
        ingredient.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserProductList(APIView):
    def get(self, request, format=None):
        products = UserProduct.objects.all()
        serializer = UserProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = UserProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProductDetail(APIView):
    def get_object(self, pk):
        try:
            return UserProduct.objects.get(pk=pk)
        except UserProduct.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        product = self.get_object(pk)
        serializer = UserProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        product = self.get_object(pk)
        serializer = UserProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        product = self.get_object(pk)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
