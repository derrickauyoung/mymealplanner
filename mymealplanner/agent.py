import vertexai
import os

# Initialize Vertex AI - use get() with defaults to avoid errors if not set
# The actual values will be set in main.py before agents are used
project = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

# Initialize Vertex AI if project is available
# Note: Models will also need explicit vertexai/project/location parameters
if project:
    vertexai.init(
        project=project,
        location=location,
    )
else:
    # Set defaults to avoid None errors (will be overridden in main.py)
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools import preload_memory
from google.adk.tools import google_search
from google.genai import types, Client
from google.adk.models.google_llm import Gemini


# Create configured client
_configured_client = Client(
    vertexai=True,
    project=project,
    location=location
)

class ConfiguredGemini(Gemini):
    """Gemini model that uses our pre-configured client."""
    
    @property
    def api_client(self):
        """Override to return our configured client."""
        return _configured_client

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


# Recipe Search Agent: Its job is to use the google_search tool and present findings.
recipe_search_agent = Agent(
    name="RecipeSearchAgent",
    model=ConfiguredGemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    ),
    instruction="""You are a specialized recipe search agent focused on finding DIVERSE recipes.

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

Focus on getting diverse, interesting recipe titles from various sources.""",
    tools=[
        google_search,
        preload_memory,
    ],
    after_agent_callback=auto_save_to_memory,  # Saves after each turn!
    output_key="recipes", # The result of this agent will be stored in the session state with this key.
)

print("✅ recipe_search_agent created.")

# Meal Plan Summarizer Agent: Its job is to summarize the text it receives.
summarizer_agent = Agent(
    name="SummarizerAgent",
    model=ConfiguredGemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config,
    ),
    # The instruction is modified to generate a google sheet with recipe and ingredients information.
    instruction="""Read the provided recipe findings: {recipes}

Combine the data into a final summary with this format:

DAY #1 (Date, Day of Week):

BREAKFAST: [Recipe Title (domain.com)](https://www.google.com/search?q=Recipe+Title+recipe)
LUNCH: [Recipe Title (domain.com)](https://www.google.com/search?q=Recipe+Title+recipe)
DINNER: [Recipe Title (domain.com)](https://www.google.com/search?q=Recipe+Title+recipe)

CRITICAL FORMATTING RULES:
1. For EACH recipe title, omit any parentheses from the title that are not surrounding a domain address \
   , and create a Markdown hyperlink in this format:
   [Recipe Title (domain.com)](https://www.google.com/search?q=Recipe+Title+recipe)
   
2. Replace spaces in the URL with + symbols
   Example: "Fluffy Pancakes (seriouseats.com)" becomes "Fluffy+Pancakes+seriouseats.com+recipe"
   
3. Always add "+recipe" to the end of the search query

4. Replace "(Date, Day of Week)" with the next day's actual date and day information, relative to the time of this query, \
    for example "(Dec-01, Monday)" if the current date and time is November 30th 2025, 10:17 PM.

5. Always replace (domain.com) with the recipe's actual source web page domain, like (seriouseats.com)

Then create a shopping list with unique ingredients and their quantities separated by Day:

DAY #1 INGREDIENTS:
- ingredient_name 1 (ingredient_quantity)
- ingredient_name 2 (ingredient_quantity)

DAY #2 INGREDIENTS:
- ingredient_name 1 (ingredient_quantity)
- ingredient_name 2 (ingredient_quantity)

Finally, provide a clickable recipe links section:

RECIPE LINKS:

DAY #1:
- [Recipe Title 1 (domain.com)](https://www.google.com/search?q=Recipe+Title+1+recipe)
- [Recipe Title 2 (domain.com)](https://www.google.com/search?q=Recipe+Title+2+recipe)
- [Recipe Title 3 (domain.com)](https://www.google.com/search?q=Recipe+Title+3+recipe)

DAY #2:
- [Recipe Title 1](https://www.google.com/search?q=Recipe+Title+1+recipe)

Make sure ALL recipe titles are clickable Google search links.""",
    tools=[preload_memory],
    output_key="final_summary",
)

print("✅ summarizer_agent created.")


# Root Agent: Orchestrates the workflow by calling the sub-agents as tools.
root_agent = SequentialAgent(
    name="MyMealPlanAgent",
    # This instruction tells the root agent HOW to use its tools (which are the other agents).
    description="""You are a friendly meal planner assistant. Your goal is to answer the user's query by orchestrating a workflow. \
1. First, you MUST call the `RecipeSearchAgent` tool to find recipes, ingredients and URLs based on the prompt provided by the user. \
2. Store the recipes result from RecipeSearchAgent. \
3. Next, you MUST call the `SummarizerAgent` tool and pass it the recipes data you received from RecipeSearchAgent. \
5. Finally, present the final_summary back to the application as your response.""",
    sub_agents=[recipe_search_agent, summarizer_agent],
    after_agent_callback=auto_save_to_memory,  # Saves after each turn!
)

print("✅ root_agent created.")