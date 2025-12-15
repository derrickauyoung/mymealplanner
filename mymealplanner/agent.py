import vertexai
import os

# Don't initialize Vertex AI here - let main.py handle it
# Just get the values for later use
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import preload_memory
from google.adk.tools import google_search
from google.genai import types, Client
from google.adk.models.google_llm import Gemini


# Create configured client lazily to avoid issues at import time
_configured_client = None

def get_configured_client():
    """Get or create the configured client with current env vars."""
    global _configured_client
    if _configured_client is None:
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        if not project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT environment variable must be set before using agents"
            )
        
        _configured_client = Client(
            vertexai=True,
            project=project,
            location=location
        )
    return _configured_client

class ConfiguredGemini(Gemini):
    """Gemini model that uses our pre-configured client."""
    def __init__(self, *args, **kwargs):
        # Extract our custom params before calling parent
        custom_model = kwargs.pop('model', 'gemini-2.5-flash-lite')
        custom_retry = kwargs.pop('retry_options', None)
        # Call parent with minimal params
        super().__init__(model=custom_model)
        # Store retry options if provided
        if custom_retry:
            self.retry_options = custom_retry
    
    @property
    def api_client(self):
        """Lazily create and return configured client."""
        return get_configured_client()

# Create a function to build agents with proper config
def create_gemini_model(model_name="gemini-2.5-flash-lite"):
    """Create a Gemini model with proper Vertex AI configuration."""
    # Use our custom ConfiguredGemini that handles client creation lazily
    return ConfiguredGemini(
        model=model_name,
        retry_options=retry_config,
    )

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )


# Agent cache for lazy loading
_agents_cache = {}

def _get_recipe_search_agent():
    """Get or create the recipe search agent lazily."""
    if 'recipe_search_agent' not in _agents_cache:
        _agents_cache['recipe_search_agent'] = Agent(
            name="RecipeSearchAgent",
            model=create_gemini_model(),
    instruction="""You are a specialized recipe search agent focused on finding DIVERSE recipes.
MEAL PLANNING STRATEGY:
1. For DAY 1 ONLY:
   - BREAKFAST: Search for a new recipe
   - LUNCH: Search for a new recipe (there are no leftovers yet!)
   - DINNER: Search for a new recipe

   DAY 1 ENTRY: Create entries like this:
    {
            "recipe_title": "Fluffy Pancakes",
            "ingredients": {"Buttermilk": "1 cup", "All-purpose flour": "2 cups"},
            "method": "Step 1: mix ingredients in bowl. Step 2: ...",
    }

2. For DAY 2 and beyond:
   - BREAKFAST: Search for a new recipe
   - LUNCH: Use "Leftovers from Day [X-1] Dinner: [Previous Dinner Recipe Name]"
   - DINNER: Search for a new recipe

3. LEFTOVER ENTRIES (Day 2+): Create entries like this WITHOUT searching:
   {
       "recipe_title": "Leftovers from Day 1 Dinner: [Exact Dinner Recipe Name]",
       "ingredients": {},
       "method": "",
   }

4. NEW RECIPE SEARCHES: Rotate between these sites for variety:
   - allrecipes.com, foodnetwork.com, simplyrecipes.com, budgetbytes.com, 
     minimalistbaker.com, seriouseats.com, bonappetit.com

5. Example output structure for 3 days (9 meals total: 6 searched, 2 leftovers):
[
    {"recipe_title": "Fluffy Pancakes", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."},  // Day 1 Breakfast
    {"recipe_title": "Mediterranean Chickpea Salad", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."},  // Day 1 Lunch (NEW)
    {"recipe_title": "Garlic Herb Roasted Chicken", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."},  // Day 1 Dinner
    
    {"recipe_title": "Berry Smoothie Bowl", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."},  // Day 2 Breakfast
    {"recipe_title": "Leftovers from Day 1 Dinner: Garlic Herb Roasted Chicken", "ingredients": {}, "method": ""},  // Day 2 Lunch
    {"recipe_title": "Vegetarian Pasta Primavera", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."},  // Day 2 Dinner
    
    {"recipe_title": "Avocado Toast", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."},  // Day 3 Breakfast
    {"recipe_title": "Leftovers from Day 2 Dinner: Vegetarian Pasta Primavera", "ingredients": {}, "method": ""},  // Day 3 Lunch
    {"recipe_title": "Beef Stir Fry", "ingredients": {}, "method": "Step 1: mix ingredients in bowl. Step 2: ..."}  // Day 3 Dinner
]

SEARCH STRATEGY FOR VARIETY:
1. Rotate between these reliable recipe sites for different meals:
   - allrecipes.com (classic recipes)
   - foodnetwork.com (chef recipes)
   - simplyrecipes.com (detailed instructions)
   - budgetbytes.com (budget-friendly)
   - minimalistbaker.com (simple recipes)
   - seriouseats.com (detailed techniques)
   - bonappetit.com (trendy, modern)

2. For each meal, use a DIFFERENT site to ensure variety:
   - "site:simplyrecipes.com breakfast recipe"
   - "site:budgetbytes.com lunch recipe"
   - "site:foodnetwork.com dinner recipe"

3. Make sure there are no duplicates!

4. Vary cuisine styles: American, Asian, Mediterranean, Mexican, etc.

5. For each search result, extract the recipe title (exact title from search result) and the ingredients and quantities (exact ingredients and quantities from search result).

6. Return a list of recipe dictionaries with the title (and the domain base address in parentheses), ingredients and quantities:
[
    {
        "recipe_title": "Fluffy Buttermilk Pancakes (simplyrecipes.com)",
        "ingredients": {
            "ingredient_name": "ingredient_quantity",
            "ingredient_name": "ingredient_quantity",
        },
    },
    {
        "recipe_title": "Mediterranean Chickpea Salad (seriouseats.com)",
        "ingredients": {
            "ingredient_name": "ingredient_quantity",
            "ingredient_name": "ingredient_quantity",
        },
    }
]

7. Only include recipes that are not already in the memory and are not already in the list of recipes.

8. Do not include empty or invalid recipes.

9. Ensure the recipe_title contains the domain base address of the recipe source in parentheses.

10. Do not accept "(as needed)", "(quantity)", "(quantity not specified)", or similar for ingredient quantities.

CRITICAL: 
- Day 1 lunch MUST be a real searched recipe
- Day 2+ lunches should be leftover references
- Include ALL meals in your output
- Focus on getting diverse, interesting recipe titles from various sources.""",
    tools=[
        google_search,
        preload_memory,
    ],
            after_agent_callback=auto_save_to_memory,  # Saves after each turn!
            output_key="recipes", # The result of this agent will be stored in the session state with this key.
        )
    return _agents_cache['recipe_search_agent']

recipe_search_agent = None  # Will be lazily loaded

def _get_json_agent():
    """Get or create the JSON agent lazily."""
    if 'json_agent' not in _agents_cache:
        _agents_cache['json_agent'] = Agent(
            name="JSONAgent",
            model=create_gemini_model(),
    instruction="""You are a meal plan data formatter. Read the recipe data from {recipes} and output ONLY a JSON object.

RECIPE DATA: {recipes}

YOUR TASK:
Convert the recipe list into a structured JSON object for the frontend:
{
  "days": [
    {
      "dayNumber": 1,
      "date": "Dec 12, 2024",
      "meals": {
        "breakfast": {
          "title": "Fluffy Pancakes (seriouseats.com)",
          "url": "https://www.google.com/search?q=Fluffy+Pancakes+recipe",
          "ingredients": {"Buttermilk": "1 cup", "All-purpose flour": "2 cups"},
          "method": "Step 1: mix ingredients in bowl. Step 2: ...",
        },
        "lunch": {
          "title": "Greek Salad (seriouseats.com)",
          "url": "https://www.google.com/search?q=Greek+Salad+recipe",
          "ingredients": {"Tomato": "1", "Cucumber": "1"},
          "method": "Step 1: mix ingredients in bowl. Step 2: ...",
        },
        "dinner": {
          "title": "Roasted Chicken (seriouseats.com)",
          "url": "https://www.google.com/search?q=Roasted+Chicken+recipe",
          "ingredients": {"Chicken": "1", "Herbs": "1 cup"},
          "method": "Step 1: mix ingredients in bowl. Step 2: ...",
        }
      }
    },
    {
      "dayNumber": 2,
      "meals": {
        "breakfast": {...},
        "lunch": {
          "title": "Leftovers from Day 1 Dinner: Roasted Chicken",
          "url": null,
          "method": "",
          "ingredients": {},
        },
        "dinner": {...}
      }
    }
  ]
}

RULES:
- Organize recipes into days (3 meals per day)
- For EACH recipe title, include the domain base address of the recipe source in parentheses, and \
   make sure to only include this text in the title itself (not the full markdown style web link): \
   Example: "Fluffy Pancakes (seriouseats.com)"
- For EACH recipe url, omit any parentheses from the title that are not surrounding a domain address \
   , and create a Markdown hyperlink in this format: \
   [Recipe Title (domain.com)](https://www.google.com/search?q=Recipe+Title+recipe)
- Replace spaces and parentheses in the URL with + symbols \
   Example: "Fluffy Pancakes (seriouseats.com)" becomes "Fluffy+Pancakes+seriouseats.com+recipe"
- Always add "+recipe" to the end of the search query
- For new recipes: create Google search URL with format `https://www.google.com/search?q=Title+recipe`
- For leftovers: set url to null
- For EACH mealtype, always include ingredients as key-value pairs with their quantities
- For EACH mealtype, always include methods as a string.
- Output ONLY the JSON object, without markdown formatting or any other text.
- Ensure the JSON object is valid and can be parsed by the frontend without errors.""",
            tools=[preload_memory],
            output_key="meal_plan_data",
        )
    return _agents_cache['json_agent']

json_agent = None  # Will be lazily loaded

# Root Agent: Orchestrates the workflow by calling the sub-agents as tools.
def _get_root_agent():
    """Get or create the root agent lazily."""
    if 'root_agent' not in _agents_cache:
        _agents_cache['root_agent'] = SequentialAgent(
            name="MyMealPlanAgent",
            # This instruction tells the root agent HOW to use its tools (which are the other agents).
            description="""You are a friendly meal planner assistant. Your goal is to answer the user's query by orchestrating a workflow. \
1. First, you MUST call the `RecipeSearchAgent` tool to find recipes, ingredients and URLs based on the prompt provided by the user. \
2. Store the recipes result from RecipeSearchAgent. \
3. Next, you MUST call the `JSONAgent` tool and pass it the recipes data you received from RecipeSearchAgent. \
5. Finally, present the meal_plan_data back to the application as your response.""",
            sub_agents=[_get_recipe_search_agent(), _get_json_agent()],
            after_agent_callback=auto_save_to_memory,  # Saves after each turn!
        )
    return _agents_cache['root_agent']

root_agent = None  # Will be lazily loaded