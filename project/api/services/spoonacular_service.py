import requests
import logging
from django.conf import settings

logger = logging.getLogger('api')

class SpoonacularService:
    def __init__(self):
        self.api_key = settings.SPOONACULAR_API_KEY
        self.base_url = settings.SPOONACULAR_BASE_URL
    