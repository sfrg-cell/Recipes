import json
import logging
import re
import google.generativeai as genai
from django.conf import settings
from api.models import Recipe

logger = logging.getLogger('api')


class GeminiNutritionService:

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        model_name = settings.GEMINI_MODEL
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')
        
        if 'latest' in model_name:
            model_name = model_name.replace('-latest', '')
        
        logger.info(f"Initializing Gemini Nutrition Service with model: {model_name}")
        self.model = genai.GenerativeModel(model_name)
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS

    def _prepare_recipe_data(self, recipe):
        
        ingredients = []
        for recipe_ingredient in recipe.ingredients.all():
            ingredients.append({
                'name': recipe_ingredient.ingredient.name,
                'quantity': float(recipe_ingredient.quantity),
                'unit': recipe_ingredient.unit.name if recipe_ingredient.unit else 'grams'
            })
        
        return {
            'id': recipe.id,
            'title': recipe.title,
            'description': recipe.description,
            'cooking_time': recipe.cooking_time,
            'servings': recipe.servings,
            'category': recipe.category.name if recipe.category else None,
            'cuisine': recipe.cuisine.name if recipe.cuisine else None,
            'complexity': recipe.complexity.name if recipe.complexity else None,
            'ingredients': ingredients,
            'instructions': recipe.instructions
        }

    def _clean_json_response(self, response_text):
        
        logger.info(f"Original response length: {len(response_text)}")
        logger.info(f"First 500 chars: {response_text[:500]}")
        
        if "```json" in response_text:
            response_text = response_text.split("```json")[1]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if "```" in response_text:
            response_text = response_text.split("```")[0]
        
        response_text = response_text.strip()
        
        if '{' in response_text and '}' in response_text:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            response_text = response_text[start_idx:end_idx]
        else:
            logger.error("No JSON braces found in response!")
            logger.error(f"Full response: {response_text}")
        
        response_text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', response_text)
        
        logger.info(f"Cleaned response length: {len(response_text)}")
        logger.info(f"Cleaned response: {response_text}")
        
        return response_text

    def calculate_calories_simple(self, recipe_id, user_question=None):
        logger.info(f"CALCULATING CALORIES FOR RECIPE {recipe_id}")
        
        try:
            recipe = Recipe.objects.get(id=recipe_id)
            recipe_data = self._prepare_recipe_data(recipe)
            
            logger.info(f"Recipe: {recipe_data['title']}")
            logger.info(f"Servings: {recipe_data['servings']}")
            logger.info(f"Ingredients count: {len(recipe_data['ingredients'])}")
            
            system_instruction = """You are a calorie calculation expert. 
You MUST return ONLY valid JSON with NO additional text, explanations, or markdown.

CRITICAL RULES:
1. Your ENTIRE response must be a single JSON object
2. NO text before the JSON
3. NO text after the JSON
4. NO markdown code blocks
5. NO explanations

Return this EXACT structure with calculated values:
{
    "total_calories": 450,
    "calories_per_serving": 225,
    "main_calorie_sources": ["ingredient1", "ingredient2"],
    "calorie_breakdown": {
        "protein_calories": 140,
        "fat_calories": 135,
        "carb_calories": 175
    },
    "answer_to_question": "Brief answer"
}

ESTIMATION GUIDELINES:
- Chicken: 165 cal/100g
- Rice (cooked): 130 cal/100g
- Vegetables: 30 cal/100g
- Olive oil: 884 cal/100g
- Pasta (cooked): 158 cal/100g
- Eggs: 155 cal/100g
- Bread: 265 cal/100g
- Cheese: 402 cal/100g"""
            
            user_message = f"""Calculate calories for this recipe.
Return ONLY JSON, nothing else.

Recipe: {recipe_data['title']}
Servings: {recipe_data['servings']}

Ingredients:
"""
            for ingredient in recipe_data['ingredients']:
                user_message += f"- {ingredient['quantity']} {ingredient['unit']} {ingredient['name']}\n"
            
            if user_question:
                user_message += f"\nUser question: {user_question}"
            
            full_prompt = f"{system_instruction}\n\n{user_message}\n\nReturn ONLY the JSON object:"
            
            logger.info("Sending request to Gemini...")
            
            max_tokens = max(2048, self.max_tokens)
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=max_tokens,
                    candidate_count=1,
                )
            )
            
            if hasattr(response, 'parts') and response.parts:
                response_text = ''.join([part.text for part in response.parts])
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)
            
            if not response_text.strip().endswith('}'):
                logger.warning("Response seems incomplete, might be truncated")
                logger.warning(f"Response ends with: ...{response_text[-50:]}")
            
            response_text = response_text.strip()
            logger.info(f"Gemini response received, length: {len(response_text)}")
            
            response_text = self._clean_json_response(response_text)
            
            try:
                calorie_data = json.loads(response_text)
                logger.info("JSON parsed successfully on first attempt")
            except json.JSONDecodeError as e:
                logger.warning(f"First JSON parse failed: {e}")
                logger.warning(f"Attempting to fix incomplete JSON...")
                
                if not response_text.endswith('}'):
                    open_braces = response_text.count('{')
                    close_braces = response_text.count('}')
                    missing_braces = open_braces - close_braces
                    
                    if missing_braces > 0:
                        response_text += '}' * missing_braces
                        logger.info(f"Added {missing_braces} closing braces")
                
                response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
                response_text = response_text.replace('\n', ' ').replace('\r', '')
                
                try:
                    calorie_data = json.loads(response_text)
                    logger.info("JSON parsed after fixing")
                except json.JSONDecodeError as e2:
                    logger.error(f"Second parse failed: {e2}")
                    logger.error(f"Response text: {response_text}")
                    
                    logger.warning("Using fallback minimal data")
                    calorie_data = {
                        'total_calories': 0,
                        'calories_per_serving': 0,
                        'main_calorie_sources': [],
                        'calorie_breakdown': {
                            'protein_calories': 0,
                            'fat_calories': 0,
                            'carb_calories': 0
                        },
                        'answer_to_question': 'Unable to calculate precise values. Please try again.'
                    }
            
            required_fields = ['total_calories', 'calories_per_serving']
            for field in required_fields:
                if field not in calorie_data:
                    logger.error(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")
            
            logger.info(f"Calories calculated: {calorie_data['total_calories']} total, {calorie_data['calories_per_serving']} per serving")
            
            return {
                'success': True,
                'recipe_id': recipe_id,
                'recipe_title': recipe.title,
                'total_calories': calorie_data.get('total_calories', 0),
                'calories_per_serving': calorie_data.get('calories_per_serving', 0),
                'main_calorie_sources': calorie_data.get('main_calorie_sources', []),
                'calorie_breakdown': calorie_data.get('calorie_breakdown', {}),
                'answer_to_question': calorie_data.get('answer_to_question', ''),
                'user_question': user_question
            }
            
        except Recipe.DoesNotExist:
            logger.error(f"Recipe with ID {recipe_id} not found")
            return {'error': 'Recipe not found', 'success': False}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response was: {response_text if 'response_text' in locals() else 'N/A'}")
            return {'error': 'AI response parsing failed', 'success': False}
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            return {'error': str(e), 'success': False}
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {'error': str(e), 'success': False}


gemini_nutrition_service = GeminiNutritionService()