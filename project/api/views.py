from api.models import (
    Recipe, MeasurementUnit, Category, Cuisine,
    Complexity, Ingredient, UserProduct, FavoriteRecipe, RecipeIngredient
)
from django.contrib.auth.models import User
from api.serializers import (
    RecipeSerializer, MeasurementUnitSerializer, CategorySerializer,
    CuisineSerializer, ComplexitySerializer, IngredientSerializer,
    UserProductSerializer, FavoriteRecipeSerializer, RecipeIngredientSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.http import Http404
from rest_framework import status
from .filters import RecipeFilter
import random
from django.db.models import Max
import logging
from api.services.gemini_service import gemini_service
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q, Count
import datetime
from api.services.ai_nutrition_service import gemini_nutrition_service

logger = logging.getLogger('api')


class RecipeSuggestions(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):

        user_ingredients = UserProduct.objects.filter(
            user = request.user
        ).values_list('ingredient', flat=True)

        if not user_ingredients:
            return Response({'error': 'User has no ingredients'}, status=status.HTTP_400_BAD_REQUEST)

        recipes = Recipe.objects.annotate(
            matching_count = Count('ingredients', filter=Q(ingredients__ingredient__in=user_ingredients))
        ).filter(matching_count__gt=0).order_by('-matching_count')[:10]

        result = []
        for recipe in recipes:
            total_ingredients = recipe.ingredients.count()

            missing_ingredients = recipe.ingredients.exclude(ingredient__in=user_ingredients).values_list('ingredient', flat=True)

            missing_names = Ingredient.objects.filter(id__in=missing_ingredients).values_list('name', flat=True)

            result.append({
                'recipe': RecipeSerializer(recipe).data,
                'matching_count': recipe.matching_count,
                'missing_ingredients': list(missing_names),
                'missing_count': len(missing_ingredients)
            })

        return Response({
            'suggestions': result
        })


class GenerateRecipeFromUserProducts(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        logger.info('POST request to GenerateRecipeFromUserProducts')
        
        try:
            user_ingredient_ids = UserProduct.objects.filter(user=request.user).values_list('ingredient_id', flat=True)
            
            user_ingredients = Ingredient.objects.filter(id__in=user_ingredient_ids).values_list('name', flat=True)

            if not user_ingredients:
                logger.warning(f"User {request.user.id} has no ingredients")
                return Response(
                    {'error': 'User has no ingredients'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            prompt = "Recipe with: " + ", ".join(user_ingredients[:10])
            
            cuisine = request.data.get('cuisine')
            complexity = request.data.get('complexity', 'easy')
            cooking_time = request.data.get('max_time')
            servings = request.data.get('servings', 2)

            recipe_data = gemini_service.generate_recipe(
                prompt=prompt,
                cuisine=cuisine,
                complexity=complexity,
                cooking_time=cooking_time,
                servings=servings,
                user_products=user_ingredients
            )
            
            recipe_data['generated_for'] = list(user_ingredients)
            recipe_data['generated_at'] = datetime.datetime.now().isoformat()
            recipe_data['user_id'] = request.user.id
            
            return Response({
                'success': True,
                'recipe': recipe_data,
                'user_ingredients': list(user_ingredients),
                'generated_at': recipe_data['generated_at']
            })

        except Exception as e:
            logger.error(f'Error: {str(e)}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
class SearchTitle(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        q = request.GET.get('q', '').lower().strip()
        
        if not q:
            return Response({'error': 'Enter search query'}, status=status.HTTP_400_BAD_REQUEST)
    
        recipes = Recipe.objects.annotate(
            similarity=TrigramSimilarity("title", q),
        ).filter(
            similarity__gt=0.1
        ).order_by("-similarity")
        
        return Response({
            'count': recipes.count(),
            'results': RecipeSerializer(recipes, many=True).data
        })


class SearchAuthor(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        q = request.GET.get('q', '').lower().strip()
        
        if not q:
            return Response({'error': 'Enter author name'}, status=status.HTTP_400_BAD_REQUEST)

        authors = User.objects.filter(username__iexact=q)

        recipes = Recipe.objects.filter(author__in=authors)

        return Response({
            'count': recipes.count(),
            'results': RecipeSerializer(recipes, many=True).data
        })


class SearchIngredient(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    SYNONYMS = [
        {'oatmeal', 'porridge', 'oats'},
        {'eggplant', 'aubergine'},
        {'zucchini', 'courgette'},
        {'cilantro', 'coriander'},
        {'tomato', 'tomatoes', 'cherry tomato'},
        {'bell pepper', 'capsicum', 'sweet pepper'},
        {'scallion', 'green onion', 'spring onion'},
    ]
    
    def get(self, request):
        q = request.GET.get('q', '').lower().strip()
        
        if not q:
            return Response({'error': 'Enter ingredient name'}, status=status.HTTP_400_BAD_REQUEST)
        
        search_terms = self.find_synonyms(q)
        
        recipes = Recipe.objects.filter(
            ingredients__ingredient__name__in=list(search_terms)
        ).distinct()
        
        return Response({
            'count': recipes.count(),
            'results': RecipeSerializer(recipes, many=True).data
        })
    
    def find_synonyms(self, q):
        for group in self.SYNONYMS:
            if q in group:
                return group
        return {q}


class RecipeList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
   
    def get(self, request, format=None):
        logger.info('GET request to RecipeList')
        try:
            recipes = Recipe.objects.all().prefetch_related('ingredients__ingredient').order_by('-created_at', 'id')
            recipe_filter = RecipeFilter(request.GET, queryset=recipes)
            filtered_recipes = recipe_filter.qs

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

            if recipe.author != request.user:
                logger.warning(f'User {request.user.username} attempted to edit recipe {pk} owned by {recipe.author.username}')
                return Response(
                    {'error': 'You do not have permission to edit this recipe'},
                    status=status.HTTP_403_FORBIDDEN
                )

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

            if recipe.author != request.user:
                logger.warning(f'User {request.user.username} attempted to delete recipe {pk} owned by {recipe.author.username}')
                return Response(
                    {'error': 'You do not have permission to delete this recipe'},
                    status=status.HTTP_403_FORBIDDEN
                )

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


class RandomRecipeWithWishes(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, format=None):
        logger.info('GET request to RandomRecipeWithWishes', extra={'filters': request.GET})
        
        try:
            recipes = Recipe.objects.all()
            
            category_id = request.GET.get('category')
            if category_id and category_id.isdigit():
                recipes = recipes.filter(category_id=int(category_id))
            
            cuisine_id = request.GET.get('cuisine')
            if cuisine_id and cuisine_id.isdigit():
                recipes = recipes.filter(cuisine_id=int(cuisine_id))
            
            complexity_id = request.GET.get('complexity')
            if complexity_id and complexity_id.isdigit():
                recipes = recipes.filter(complexity_id=int(complexity_id))
            
            max_time = request.GET.get('max_time')
            if max_time and max_time.isdigit():
                recipes = recipes.filter(cooking_time__lte=int(max_time))
            
            min_rating = request.GET.get('min_rating')
            if min_rating:
                try:
                    recipes = recipes.filter(rating__gte=float(min_rating))
                except ValueError:
                    pass
            
            servings = request.GET.get('servings')
            if servings and servings.isdigit():
                recipes = recipes.filter(servings=int(servings))
            
            ingredients_param = request.GET.get('ingredients')
            if ingredients_param:
                try:
                    ingredient_ids = [int(id.strip()) for id in ingredients_param.split(',')]
                    recipes = recipes.filter(ingredients__ingredient__id__in=ingredient_ids).distinct()
                except ValueError:
                    pass
            
            total_filtered = recipes.count()
            logger.debug(f'Found {total_filtered} recipes after filtering')
            
            if total_filtered == 0:
                logger.warning('No recipes found with applied filters')
                return Response({
                    'error': 'No recipes found for your criteria',
                    'filters_used': {
                        'category': category_id,
                        'cuisine': cuisine_id,
                        'complexity': complexity_id,
                        'max_time': max_time,
                        'min_rating': min_rating,
                        'servings': servings,
                        'ingredients': ingredients_param
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            max_id = recipes.aggregate(max_id=Max("id"))['max_id']
            
            for attempt in range(10):
                random_id = random.randint(1, max_id)
                random_recipe = recipes.filter(id=random_id).first()
                if random_recipe:
                    logger.info(f'Random recipe with filters found on attempt {attempt + 1}: {random_recipe.title}')
                    serializer = RecipeSerializer(random_recipe)
                    
                    return Response({
                        'recipe': serializer.data,
                        'filters_info': {
                            'total_available': total_filtered,
                            'applied_filters': {
                                'category': category_id,
                                'cuisine': cuisine_id,
                                'complexity': complexity_id,
                                'max_time': max_time,
                                'min_rating': min_rating,
                                'servings': servings,
                                'ingredients': ingredients_param
                            } if any([category_id, cuisine_id, complexity_id, max_time, min_rating, servings, ingredients_param]) else None
                        }
                    })
            
            fallback_recipe = recipes.first()
            if fallback_recipe:
                serializer = RecipeSerializer(fallback_recipe)
                return Response({'recipe': serializer.data})
            
            return Response({'error': 'No recipes found'}, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f'Error in RandomRecipeWithWishes: {str(e)}')
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            products = UserProduct.objects.filter(user=request.user)
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
                serializer.save(user=request.user)
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


class FavoriteRecipeList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        logger.info('GET request to FavoriteRecipeList', extra={'user': request.user.username})
        try:
            favorites = FavoriteRecipe.objects.filter(user=request.user).select_related('recipe')
            logger.debug(f'Found {favorites.count()} favorite recipes')
            serializer = FavoriteRecipeSerializer(favorites, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f'Error in FavoriteRecipeList GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request, format=None):
        logger.info('POST request to FavoriteRecipeList', extra={'user': request.user.username})
        try:
            serializer = FavoriteRecipeSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                logger.info('Recipe added to favorites successfully')
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            logger.warning(f'Favorite recipe validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'Error in FavoriteRecipeList POST: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FavoriteRecipeDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return FavoriteRecipe.objects.get(pk=pk, user=user)
        except FavoriteRecipe.DoesNotExist:
            logger.warning(f'Favorite recipe with id {pk} not found for user {user.username}')
            raise Http404

    def delete(self, request, pk, format=None):
        logger.info(f'DELETE request for favorite recipe {pk}', extra={'user': request.user.username})
        try:
            favorite = self.get_object(pk, request.user)
            favorite.delete()
            logger.info(f'Favorite recipe {pk} removed successfully')
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error(f'Error in FavoriteRecipeDetail DELETE: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckFavoriteRecipe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, recipe_id, format=None):
        logger.info(f'GET request to check if recipe {recipe_id} is favorite', extra={'user': request.user.username})
        try:
            is_favorite = FavoriteRecipe.objects.filter(user=request.user, recipe_id=recipe_id).exists()
            favorite_id = None
            if is_favorite:
                favorite = FavoriteRecipe.objects.get(user=request.user, recipe_id=recipe_id)
                favorite_id = favorite.id

            return Response({
                'is_favorite': is_favorite,
                'favorite_id': favorite_id
            })

        except Exception as e:
            logger.error(f'Error in CheckFavoriteRecipe: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RecipeIngredientList(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, recipe_id, format=None):
        logger.info(f'POST request to add ingredient to recipe {recipe_id}', extra={'user': request.user.username})
        try:
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
            except Recipe.DoesNotExist:
                return Response(
                    {'error': 'Recipe not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            data = request.data.copy()
            data['recipe'] = recipe_id

            serializer = RecipeIngredientSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                logger.info(f'Ingredient added to recipe {recipe_id} successfully')
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            logger.warning(f'Recipe ingredient validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f'Error in RecipeIngredientList POST: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserRecipeList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        logger.info('GET request to UserRecipeList', extra={'user': request.user.username})
        try:
            recipes = Recipe.objects.filter(author=request.user).prefetch_related('ingredients__ingredient').order_by('-created_at', 'id')
            logger.debug(f'Found {recipes.count()} recipes for user {request.user.username}')
            serializer = RecipeSerializer(recipes, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f'Error in UserRecipeList GET: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        
class RecipeGeminiNutritionView(APIView):
    
    def get(self, request, recipe_id):
        logger.info(f"GET request for recipe {recipe_id} nutrition")
        
        try:
            result = gemini_nutrition_service.calculate_calories_simple(
                recipe_id=recipe_id,
                user_question=None
            )
            
            logger.info(f"Result success: {result.get('success')}")
            
            if not result.get('success'):
                logger.error(f"Error in result: {result.get('error')}")
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Exception in GET: {e}", exc_info=True)
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, recipe_id):
        logger.info(f"POST request for recipe {recipe_id} nutrition")
        
        try:
            user_prompt = request.data.get('prompt', '')
            
            if 'calor' in user_prompt.lower() or 'calor' in user_prompt.lower():
                result = gemini_nutrition_service.calculate_calories_simple(
                    recipe_id=recipe_id,
                    user_question=user_prompt
                )
            else:
                result = gemini_nutrition_service.analyze_recipe_nutrition(
                    recipe_id=recipe_id,
                    user_prompt=user_prompt
                )
            
            if not result.get('success'):
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Exception in POST: {e}", exc_info=True)
            return Response({
                'error': str(e),
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)