from django.urls import path
from api import views

urlpatterns = [
    path('recipes/', views.RecipeList.as_view()),
    path('recipes/<int:pk>/', views.RecipeDetail.as_view()),

    path('units/', views.MeasurementUnitList.as_view()),
    path('categories/', views.CategoryList.as_view()),
    path('cuisines/', views.CuisineList.as_view()),
    path('complexities/', views.ComplexityList.as_view()),

    path('ingredients/', views.IngredientList.as_view()),
    path('ingredients/<int:pk>/', views.IngredientDetail.as_view()),

    path('user-products/', views.UserProductList.as_view()),
    path('user-products/<int:pk>/', views.UserProductDetail.as_view()),
]
