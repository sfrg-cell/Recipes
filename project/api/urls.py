from django.urls import path
from api import views

urlpatterns = [
    path('recipes/', views.RecipeList.as_view()),

    path('recipes/random/', views.RandomRecipe.as_view(), name='random-recipe'),
    path('recipes/generate/', views.GenerateRecipe.as_view(), name='generate-recipe'),

    path('recipes/random/', views.RandomRecipe.as_view()),
    path('recipes/random-with-wishes/', views.RandomRecipeWithWishes.as_view(), name='random-recipe-with-wishes'),

    path('recipes/<int:pk>/', views.RecipeDetail.as_view()),
    path('recipes/<int:recipe_id>/check-favorite/', views.CheckFavoriteRecipe.as_view(), name='check-favorite'),
    path('recipes/<int:recipe_id>/ingredients/', views.RecipeIngredientList.as_view(), name='recipe-ingredients'),

    path('recipes/search/title/', views.SearchTitle.as_view()),
    path('recipes/search/author/', views.SearchAuthor.as_view()),
    path('recipes/search/ingredient/', views.SearchIngredient.as_view()),

    path('units/', views.MeasurementUnitList.as_view()),
    path('categories/', views.CategoryList.as_view()),
    path('cuisines/', views.CuisineList.as_view()),
    path('complexities/', views.ComplexityList.as_view()),

    path('ingredients/', views.IngredientList.as_view()),
    path('ingredients/<int:pk>/', views.IngredientDetail.as_view()),

    path('user-products/', views.UserProductList.as_view()),
    path('user-products/<int:pk>/', views.UserProductDetail.as_view()),
    
    path('favorites/', views.FavoriteRecipeList.as_view(), name='favorite-list'),
    path('favorites/<int:pk>/', views.FavoriteRecipeDetail.as_view(), name='favorite-detail'),

    path('suggestions/', views.RecipeSuggestions.as_view()),
    path('suggestions_ai/', views.GenerateRecipeFromUserProducts.as_view())
]
