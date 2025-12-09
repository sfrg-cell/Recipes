import json
import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger('api')


class GeminiService:

    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)

        model_name = settings.GEMINI_MODEL
        if model_name.startswith('models/'):
            model_name = model_name.replace('models/', '')

        if 'latest' in model_name:
            model_name = model_name.replace('-latest', '')

        logger.info(f"Initializing Gemini with model: {model_name}")
        self.model = genai.GenerativeModel(model_name)
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_TOKENS

    def generate_recipe(self, prompt, cuisine=None, complexity=None, cooking_time=None, servings=None, user_products=None):
        logger.info(f"Generating recipe for: {prompt}")

        try:
            system_instruction = """You are a professional chef specializing in SIMPLE, EASY-TO-MAKE recipes. Generate recipes in JSON format ONLY.
Your response must be ONLY a valid JSON object with this exact structure:
{
    "title": "Recipe Name",
    "description": "Brief description (2-3 sentences)",
    "cooking_time": 30,
    "servings": 4,
    "complexity": "easy",
    "cuisine": "Italian",
    "category": "Main Course",
    "ingredients": [
        {"name": "Ingredient", "quantity": "200", "unit": "grams"}
    ],
    "instructions": "Step-by-step instructions"
}

CRITICAL RULES:
- Return ONLY valid JSON, no markdown, no explanation, no additional text
- All string values MUST be properly escaped (no unescaped quotes or newlines in strings)
- Use \\n for newlines inside strings, not actual newlines
- complexity must be EXACTLY one of: "easy", "medium", or "hard"
- cooking_time and servings are integers (numbers without quotes)
- ingredients is an array of objects with name, quantity, and unit
- instructions should be a single string with steps separated by \\n
- Ensure all JSON strings are properly closed with quotes

RECIPE SIMPLICITY REQUIREMENTS:
- ALWAYS prefer "easy" complexity unless explicitly requested otherwise
- Keep ingredient list SHORT (5-10 ingredients maximum)
- Use SIMPLE cooking techniques (no advanced culinary skills required)
- Instructions should be CLEAR and CONCISE (3-7 steps maximum)
- Avoid exotic ingredients or hard-to-find items
- Focus on quick, everyday recipes that anyone can make"""

            user_message = f"Create a SIMPLE and EASY recipe for: {prompt}"

            if user_products:
                user_message += f"\n\nIMPORTANT - Available ingredients (use ONLY these if possible): {', '.join(user_products)}"
                user_message += "\nTry to use ONLY the ingredients from the list above. You may add common basics (salt, pepper, oil) if absolutely necessary, but avoid adding other ingredients."

            if cuisine:
                user_message += f"\nCuisine: {cuisine}"
            if complexity:
                user_message += f"\nComplexity: {complexity}"
            else:
                user_message += f"\nComplexity: easy"
            if cooking_time:
                user_message += f"\nMax cooking time: {cooking_time} minutes"
            if servings:
                user_message += f"\nServings: {servings}"

            full_prompt = f"{system_instruction}\n\n{user_message}"

            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )

            response_text = response.text.strip()

            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            if '{' in response_text and '}' in response_text:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                response_text = response_text[start_idx:end_idx]

            try:
                recipe_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.warning(f"First JSON parse attempt failed: {e}")
                logger.debug(f"Problematic response (first 500 chars): {response_text[:500]}")

                import re
                response_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', response_text)
                recipe_data = json.loads(response_text)

            logger.info(f"Recipe generated: {recipe_data.get('title')}")
            return recipe_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON after all attempts: {e}")
            logger.error(f"Response text (first 1000 chars): {response_text[:1000] if 'response_text' in locals() else 'N/A'}")
            raise Exception(f"Invalid JSON response from Gemini. Please try again or adjust the prompt.")
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            raise Exception(f"Failed to generate recipe: {str(e)}")


gemini_service = GeminiService()
