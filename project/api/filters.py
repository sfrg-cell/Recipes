import django_filters
from api.models import Recipe
from fuzzywuzzy import process


class RecipeFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    search = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    complexity = django_filters.NumberFilter(field_name='complexity__id')
    cuisine = django_filters.NumberFilter(field_name='cuisine__id')
    category = django_filters.NumberFilter(field_name='category__id')
    author = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    cooking_time = django_filters.NumberFilter(field_name='cooking_time', lookup_expr='exact')
    servings = django_filters.NumberFilter(field_name='servings', lookup_expr='exact')
    rating = django_filters.NumberFilter(field_name='rating', lookup_expr='exact')
    max_cooking_time = django_filters.NumberFilter(field_name='cooking_time', lookup_expr='lte')
    min_cooking_time = django_filters.NumberFilter(field_name='cooking_time', lookup_expr='gte')

    class Meta:
        model = Recipe
        fields = [
            'title', 'search', 'complexity', 'cuisine', 'category', 'author',
            'cooking_time', 'servings', 'rating'
            ]


def fuzzy_search(queryset, search_term, threshold=70):
    objects = list(queryset)
    if not objects:
        return []

    search_data = []
    for obj in objects:
        text_parts = [obj.title]

        ingredients = [ing.ingredient.name for ing in obj.ingredients.all()]
        text_parts.extend(ingredients)

        search_data.append(' '.join(text_parts))

    matches = process.extract(search_term, search_data, limit=20)

    results = []
    for match in matches:
        text, score = match
        if score >= threshold:
            index = search_data.index(text)
            results.append(objects[index])

    return results
