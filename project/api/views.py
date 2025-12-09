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
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly

from django.http import Http404
from rest_framework import status
from .filters import RecipeFilter, fuzzy_search
import random
from django.db.models import Max
import logging
from api.services.gemini_service import gemini_service

logger = logging.getLogger('api')


class RecipeList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
   
    def get(self, request, format=None):
        logger.info('GET request to RecipeList')
        try:
            recipes = Recipe.objects.all().prefetch_related('ingredients__ingredient').order_by('-created_at', 'id')
            recipe_filter = RecipeFilter(request.GET, queryset=recipes)
            filtered_recipes = recipe_filter.qs
            fuzzy_search_term = request.GET.get('fuzzy_search')
            if fuzzy_search_term:
                filtered_recipes = fuzzy_search(filtered_recipes, fuzzy_search_term)

            paginator = LimitOffsetPagination()
            paginated_recipes = paginator.paginate_queryset(filtered_recipes, request)
            serializer = RecipeSerializer(paginated_recipes, many=True)

            logger.debug(f'Found {len(filtered_recipes)} recipes after filtering, returning page with {len(paginated_recipes)} recipes')
            return paginator.get_paginated_response(serializer.data)

        except Exception as e:
            logger.error(f'Error in RecipeList GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        logger.info('POST request to RecipeList', extra={'user': request.user.username})
        try:
            serializer = RecipeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info('Recipe created successfully')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            logger.warning(f'Recipe validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in RecipeList POST: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecipeDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_object(self, pk):
        try:
            return Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            logger.warning(f'Recipe with id {pk} not found')
            raise Http404

    def get(self, request, pk, format=None):
        logger.info(f'GET request for recipe {pk}')
        try:
            recipe = self.get_object(pk)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in RecipeDetail GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk, format=None):
        logger.info(f'PUT request for recipe {pk}', extra={'user': request.user.username})
        try:
            recipe = self.get_object(pk)
            serializer = RecipeSerializer(recipe, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f'Recipe {pk} updated successfully')
                return Response(serializer.data)
            
            logger.warning(f'Recipe {pk} update validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in RecipeDetail PUT: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk, format=None):
        logger.info(f'DELETE request for recipe {pk}', extra={'user': request.user.username})
        try:
            recipe = self.get_object(pk)
            recipe.delete()
            logger.info(f'Recipe {pk} deleted successfully')
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f'Error in RecipeDetail DELETE: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RandomRecipe(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, format=None):
        logger.info('GET request to RandomRecipe')
        try:
            max_id = Recipe.objects.aggregate(max_id=Max("id"))['max_id']
            logger.debug(f'Max recipe ID: {max_id}')
            
            if max_id is None:
                logger.warning('No recipes found in database')
                return Response({'error': 'No recipes found'}, status=status.HTTP_404_NOT_FOUND)
            
            for attempt in range(10):
                random_id = random.randint(1, max_id)
                random_recipe = Recipe.objects.filter(id=random_id).first()
                if random_recipe:
                    logger.info(f'Random recipe found on attempt {attempt + 1}: {random_recipe.title}')
                    serializer = RecipeSerializer(random_recipe)
                    return Response(serializer.data)
                
            logger.warning('Random recipe not found in 10 attempts, using fallback')
            fallback_recipe = Recipe.objects.first()

            if fallback_recipe:
                logger.info(f'Using fallback recipe: {fallback_recipe.title}')
                serializer = RecipeSerializer(fallback_recipe)
                return Response(serializer.data)
            
            logger.error('No recipes available even for fallback')
            return Response({'error': 'No recipes found'}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f'Error in RandomRecipe: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
   

class MeasurementUnitList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, format=None):
        logger.info('GET request to MeasurementUnitList')
        try:
            units = MeasurementUnit.objects.all()
            logger.debug(f'Found {units.count()} measurement units')
            serializer = MeasurementUnitSerializer(units, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in MeasurementUnitList: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CategoryList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, format=None):
        logger.info('GET request to CategoryList')
        try:
            categories = Category.objects.all()
            logger.debug(f'Found {categories.count()} categories')
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in CategoryList: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CuisineList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, format=None):
        logger.info('GET request to CuisineList')
        try:
            cuisines = Cuisine.objects.all()
            logger.debug(f'Found {cuisines.count()} cuisines')
            serializer = CuisineSerializer(cuisines, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in CuisineList: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComplexityList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, format=None):
        logger.info('GET request to ComplexityList')
        try:
            complexities = Complexity.objects.all()
            logger.debug(f'Found {complexities.count()} complexity levels')
            serializer = ComplexitySerializer(complexities, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in ComplexityList: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IngredientList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request, format=None):
        logger.info('GET request to IngredientList')
        try:
            ingredients = Ingredient.objects.all()
            logger.debug(f'Found {ingredients.count()} ingredients')
            serializer = IngredientSerializer(ingredients, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in IngredientList GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        logger.info('POST request to IngredientList', extra={'user': request.user.username})
        try:
            serializer = IngredientSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info('Ingredient created successfully')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            logger.warning(f'Ingredient validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in IngredientList POST: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IngredientDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_object(self, pk):
        try:
            return Ingredient.objects.get(pk=pk)
        except Ingredient.DoesNotExist:
            logger.warning(f'Ingredient with id {pk} not found')
            raise Http404

    def get(self, request, pk, format=None):
        logger.info(f'GET request for ingredient {pk}')
        try:
            ingredient = self.get_object(pk)
            serializer = IngredientSerializer(ingredient)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in IngredientDetail GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk, format=None):
        logger.info(f'PUT request for ingredient {pk}', extra={'user': request.user.username})
        try:
            ingredient = self.get_object(pk)
            serializer = IngredientSerializer(ingredient, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f'Ingredient {pk} updated successfully')
                return Response(serializer.data)
            
            logger.warning(f'Ingredient {pk} update validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in IngredientDetail PUT: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk, format=None):
        logger.info(f'DELETE request for ingredient {pk}', extra={'user': request.user.username})
        try:
            ingredient = self.get_object(pk)
            ingredient.delete()
            logger.info(f'Ingredient {pk} deleted successfully')
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Exception as e:
            logger.error(f'Error in IngredientDetail DELETE: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProductList(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, format=None):
        logger.info('GET request to UserProductList', extra={'user': request.user.username})
        try:
            products = UserProduct.objects.all()
            logger.debug(f'Found {products.count()} user products')
            serializer = UserProductSerializer(products, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in UserProductList GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        logger.info('POST request to UserProductList', extra={'user': request.user.username})
        try:
            serializer = UserProductSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info('User product created successfully')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            logger.warning(f'User product validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in UserProductList POST: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserProductDetail(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk):
        try:
            return UserProduct.objects.get(pk=pk)
        except UserProduct.DoesNotExist:
            logger.warning(f'User product with id {pk} not found')
            raise Http404

    def get(self, request, pk, format=None):
        logger.info(f'GET request for user product {pk}', extra={'user': request.user.username})
        try:
            product = self.get_object(pk)
            serializer = UserProductSerializer(product)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f'Error in UserProductDetail GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk, format=None):
        logger.info(f'PUT request for user product {pk}', extra={'user': request.user.username})
        try:
            product = self.get_object(pk)
            serializer = UserProductSerializer(product, data=request.data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f'User product {pk} updated successfully')
                return Response(serializer.data)
            
            logger.warning(f'User product {pk} update validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in UserProductDetail PUT: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk, format=None):
        logger.info(f'DELETE request for user product {pk}', extra={'user': request.user.username})
        try:
            product = self.get_object(pk)
            product.delete()
            logger.info(f'User product {pk} deleted successfully')
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f'Error in UserProductDetail DELETE: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateRecipe(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        logger.info('POST request to GenerateRecipe', extra={'user': request.user.username})
        try:
            prompt = request.data.get('prompt')
            if not prompt:
                return Response(
                    {'error': 'prompt is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            cuisine = request.data.get('cuisine')
            complexity = request.data.get('complexity')
            cooking_time = request.data.get('cooking_time')
            servings = request.data.get('servings')
            use_user_products = request.data.get('use_user_products', False)

            user_products = None
            if use_user_products:
                user_products_qs = UserProduct.objects.filter(user=request.user)
                if user_products_qs.exists():
                    user_products = [up.ingredient.name for up in user_products_qs]
                    logger.info(f'Using {len(user_products)} user products for recipe generation')

            logger.info(f'Generating recipe with prompt: {prompt}')
            recipe_data = gemini_service.generate_recipe(
                prompt=prompt,
                cuisine=cuisine,
                complexity=complexity,
                cooking_time=cooking_time,
                servings=servings,
                user_products=user_products
            )

            logger.info(f'Recipe generated successfully: {recipe_data.get("title")}')
            return Response(recipe_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f'Error in GenerateRecipe POST: {str(e)}', exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
