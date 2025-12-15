"""
Google Cloud Functions entry point for My Meal Planner API.
This can be deployed to Cloud Run or Cloud Functions.
"""
import json
import os
import asyncio
from flask import Flask, request, jsonify, send_from_directory, render_template
import vertexai

# Initialize Vertex AI FIRST, before importing agents
# This ensures models have the correct configuration
project = os.environ.get("GOOGLE_CLOUD_PROJECT")
location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

if not project:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT environment variable is required. "
        "Please set it with: export GOOGLE_CLOUD_PROJECT=your-project-id"
    )

# Initialize Vertex AI with explicit parameters BEFORE importing agents
vertexai.init(
    project=project,
    location=location,
)

# Now import ADK components and agents (they will use the initialized Vertex AI)
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from mymealplanner.agent import _get_root_agent

from mymealplanner.agent_utils import run_session


app = Flask(__name__,
            static_folder='static',
            static_url_path='/static',
            template_folder='templates')


CORS_ALLOWED_ORIGIN = os.environ.get('CORS_ALLOWED_ORIGIN', 'https://derrickauyoung.github.io')


@app.after_request
def add_cors_headers(response):
    # Ensure we return a concrete origin (cannot be '*' when credentials are used)
    response.headers['Access-Control-Allow-Origin'] = CORS_ALLOWED_ORIGIN
    response.headers['Vary'] = 'Origin'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@app.route('/', methods=['GET', 'OPTIONS'])
def index():
    """Serve the main index.html file."""
    if request.method == "OPTIONS":
        return ('', 204)
    return render_template('index.html')


# SPA-safe catch-all: serve real static assets, otherwise return index.html
@app.route('/path:path', methods=['GET','OPTIONS'])
def serve_frontend(path):
    # Preflight
    if request.method == 'OPTIONS':
        return ('', 204)

    # If path is explicitly for static assets, serve them from static folder.
    # - path starting with 'static/' OR path contains a file extension -> treat as static asset
    if path.startswith(app.static_url_path.lstrip('/')) or os.path.splitext(path)[1]:
        # normalize path to avoid directory traversal
        safe_path = path
        if safe_path.startswith('..') or os.path.isabs(safe_path):
            return jsonify({"error": "Invalid path"}), 400
        return send_from_directory(app.static_folder, safe_path)

    # If you have API routes under /api/*, make sure they are registered before this catch-all.
    # This fallback is for SPA client-side routes: return index.html
    return render_template('index.html')


@app.route('/health', methods=['GET', 'OPTIONS'])
def health():
    """Health check endpoint."""
    if request.method == 'OPTIONS':
        # Preflight request
        return '', 204
    return jsonify({"status": "healthy"}), 200


@app.route('/plan-meals', methods=['POST', 'OPTIONS'])
def generate_meal_plan():
    """
    Endpoint to generate a meal plan based on the number of days provided.
    Expects JSON with 'days' field.
    """
    if request.method == 'OPTIONS':
        # Preflight request
        return '', 204
    
    try:
        data = request.json
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Ensure Vertex AI is properly initialized
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        if not project:
            return jsonify({
                "error": "GOOGLE_CLOUD_PROJECT environment variable is required"
            }), 500
        
        try:
            vertexai.init(project=project, location=location)
        except Exception as e:
            print(f"Warning: Vertex AI already initialized: {e}")
        
        print(f"Using Vertex AI with project: {project}, location: {location}")
                
        # Define async function that creates everything fresh
        async def run_plan():
            # Create NEW session and memory services for THIS request
            session_service = InMemorySessionService()
            memory_service = InMemoryMemoryService()
            
            # Create NEW runner for THIS request
            auto_runner = Runner(
                agent=_get_root_agent(),
                app_name="agents",
                session_service=session_service,
                memory_service=memory_service,
            )
            
            # Run the session
            return await run_session(
                auto_runner,
                session_service,
                prompt,
                app_name="agents",
                user_id="api_user",
                session_id=f"session_{hash(prompt) % 10000}"
            )
        
        # Run with asyncio.run() which creates a fresh event loop
        structured_data = asyncio.run(run_plan())
        
        # Parse if it's a string
        if structured_data and isinstance(structured_data, str):
            import json
            import re
            
            # Remove markdown code fences if present
            cleaned_data = structured_data.strip()
            
            # Remove ```json and ``` if present
            if cleaned_data.startswith('```'):
                # Remove opening fence (```json or just ```)
                cleaned_data = re.sub(r'^```(?:json)?\s*\n', '', cleaned_data)
                # Remove closing fence
                cleaned_data = re.sub(r'\n```\s*$', '', cleaned_data)
                cleaned_data = cleaned_data.strip()
            try:
                structured_data = json.loads(cleaned_data)

            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw string: {cleaned_data[:500]}")  # Print first 500 chars
                return jsonify({
                    "error": "Invalid JSON from agent",
                    "raw_data": cleaned_data[:1000]
                }), 500

        return jsonify({
            "status": "success",
            "summary": structured_data,
            "structured_data": structured_data
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in generate_meal_plan: {error_details}")
        return jsonify({
            "error": str(e),
            "details": error_details
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

