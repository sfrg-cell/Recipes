# Recipes
### Developers: Ioanna Havryliuk, Poremska Liudmyla, Oleksandr Rozheliuk

## Overview
Recipe is a RESTful API built with Django and PostgreSQL, designed for modern recipe management. The platform integrates Google Gemini AI for smart recipe generation, Spoonacular for financial analysis, and AWS S3 for scalable media storage. Users can manage their personal pantries, receive tailored cooking suggestions, and use advanced search filters to find their next meal.

## Tech Stack
- Framework: Django 5.2.7, Django REST Framework 3.16.1
- Database: PostgreSQL
- Storage: AWS S3
- AI: Google Gemini AI
- Third-party API: Spoonacular
- Authentication: JWT (SimpleJWT)
- Documentation: Swagger (drf-yasg)

## Key Features
1. Advanced Search and Filtering

    - Fuzzy Search: Implementation of title and ingredient search that accounts for variations and partial matches.

    - Filter System: Filter recipes by category, cuisine, complexity, and cooking time.

    - Author-based Search: Ability to filter recipes created by specific users.

2. AI Recipe Generation

    - Integration with Google Gemini AI to generate full recipes based on user-provided parameters or available ingredients.

3. Pantry and Smart Suggestions

    - User Pantry: Users can maintain a digital inventory of their products with quantities and expiration dates.

    - Matching Algorithm: The system suggests recipes that can be cooked based on the ingredients currently available in the user's pantry.

4. External Integrations

    - Spoonacular: Used for calculating the estimated price of recipes and providing detailed ingredient information.

    - AWS S3: All uploaded recipe images are stored and served via Amazon S3 for production-ready media handling.

5. Secure Authentication

    - Full JWT-based authentication system.

    - Role-based access control for creating, editing, and managing recipes.


## Data Model
The system uses a normalized relational structure:

    Recipe: Core model including title, instructions, image, and rating.
    
    Ingredient & RecipeIngredient: Handles many-to-many relationships with specific quantities and units.
    
    UserProduct: Manages the user's inventory.
    
    FavoriteRecipe: Allows users to save and track their preferred dishes.
    
    Support Models: Category, Cuisine, Complexity, and MeasurementUnit for strict data categorization.

## Installation
Prerequisites

    Python 3.10+

    PostgreSQL

    AWS S3 Bucket

    API Keys for Gemini and Spoonacular

## Setup

Clone the repository:

    git clone (https://github.com/sfrg-cell/Recipes.git)
    cd recipes

Install dependencies:

    pip install -r requirements.txt

Configure Environment Variables:

    Create a .env file in the root directory:

    DB_NAME=your_db
    DB_USER=your_user
    DB_PASSWORD=your_password
    GEMINI_API_KEY=your_key
    GEMINI_MODEL=gemini-pro
    SPOONACULAR_API_KEY=your_key
    AWS_ACCESS_KEY_ID=your_aws_key
    AWS_SECRET_ACCESS_KEY=your_aws_secret
    AWS_STORAGE_BUCKET_NAME=your_bucket

Initialize Database:

    python manage.py migrate

Run the Server:

    python manage.py runserver

## API Documentation

Once the server is running, you can access the interactive API documentation at:

    Swagger UI: /swagger/


## Logging

The application maintains detailed logs located in logs/recipes.log. It tracks system info, errors, and custom API events for debugging and monitoring.
