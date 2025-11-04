import django_filters
from api.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    complexity = django_filters.CharFilter(field_name='complexity__name', lookup_expr='icontains')
    cuisine = django_filters.CharFilter(field_name='cuisine__name', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    author = django_filters.CharFilter(field_name='author__name', lookup_expr='icontains')
    cooking_time = django_filters.CharFilter(field_name='cooking_time__name', lookup_expr='icontains')
    servings = django_filters.CharFilter(field_name='servings__name', lookup_expr='icontains')
    rating = django_filters.CharFilter(field_name='rating__name', lookup_expr='icontains')
    max_cooking_time = django_filters.NumberFilter(field_name='cooking_time', lookup_expr='lte')
    min_cooking_time = django_filters.NumberFilter(field_name='cooking_time', lookup_expr='gte')

    class Meta:
        model = Recipe
        fields = [
            'title', 'complexity', 'cuisine', 'category', 'author',
            'cooking_time', 'servings', 'rating'
            ]
