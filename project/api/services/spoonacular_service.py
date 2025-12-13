import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('api')

class SpoonacularService:
    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        self.base_url = settings.SPOONACULAR_BASE_URL
    
    def get_ingredient_price(self, ingredient_name, quantity=None, unit=None):
        cache_key = f"price_{ingredient_name.lower()}"
        
        if quantity is None:
            quantity = 100
            unit = 'grams'

        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            search_url = f"{self.base_url}/food/ingredients/search"
            params = {
                'query': ingredient_name,
                'apiKey': self.api_key,
                'number': 1
            }
            
            search_response = requests.get(search_url, params=params, timeout=5)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                
                if search_data.get('results'):
                    ingredient_id = search_data['results'][0]['id']
                    
                    info_url = f"{self.base_url}/food/ingredients/{ingredient_id}/information"
                    info_params = {
                        'amount': 100,
                        'unit': 'grams',
                        'apiKey': self.api_key
                    }
                    
                    info_response = requests.get(info_url, params=info_params, timeout=5)
                    
                    if info_response.status_code == 200:
                        info_data = info_response.json()
                        
                        estimated_cost = info_data.get('estimatedCost', {})
                        price_cents = estimated_cost.get('value', 300)
                        
                        price_usd = price_cents / 100
                        
                        result = {
                            'name': ingredient_name,
                            'price_usd': round(price_usd, 2),
                            'source': 'spoonacular'
                        }
                        
                        cache.set(cache_key, result, 604800)
                        return result
            
            default_price = self.get_default_price(ingredient_name)
            return default_price
            
        except Exception as e:
            logger.error(f"Spoonacular error for {ingredient_name}: {str(e)}")
            default_price = self.get_default_price(ingredient_name)
            return default_price
    
    def get_default_price(self, ingredient_name):
        price = 2.50
        
        result = {
            'name': ingredient_name,
            'price_usd': price,
            'source': 'default'
        }
        
        cache_key = f"price_{ingredient_name.lower()}"
        cache.set(cache_key, result, 86400)
        
        return result
    
    def get_prices_for_list(self, ingredient_names):
        return [self.get_ingredient_price(name) for name in ingredient_names]

spoonacular_service = SpoonacularService()