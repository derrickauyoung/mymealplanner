"""
Google Cloud Functions entry point for My Meal Planner API.
This can be deployed to Cloud Run or Cloud Functions.
"""
import json
import os
import asyncio
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import vertexai
import re
from datetime import datetime, timedelta

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
from google.genai import types
from mymealplanner.agent import root_agent

from mymealplanner.agent_utils import run_session
from mymealplanner.web_utils import parse_summary_to_structured_data

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(
    app,
    resources={r"/*": {"origins": "https://derrickauyoung.github.io"}},
    supports_credentials=False,
    allow_headers=["Content-Type"],
    methods=["GET", "POST", "OPTIONS"]
)

@app.route('/', methods=['GET', 'OPTIONS'])
def index():
    """Serve the main index.html file."""
    if request.method == 'OPTIONS':
        return '', 204
    return send_file('index.html')

@app.route('/<path:path>', methods=['GET', 'OPTIONS'])
def serve_static(path):
    """Serve static files (images, etc.)"""
    if request.method == 'OPTIONS':
        return '', 204
    if path.startswith('resources/'):
        return send_from_directory('.', path)
    # For any other path, try to serve as static file
    try:
        return send_from_directory('.', path)
    except:
        # If file doesn't exist, return index.html for SPA routing
        return send_file('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"}), 200


@app.route('/plan', methods=['POST', 'OPTIONS'])
def plan_meals():
    """
    Main endpoint to generate a meal plan.
    Expects JSON with 'prompt' field.
    """
    if request.method == 'OPTIONS':
        # Preflight request
        return '', 204
    
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Ensure Vertex AI is properly initialized
        # Re-initialize to make sure it's set up correctly
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        if not project:
            return jsonify({
                "error": "GOOGLE_CLOUD_PROJECT environment variable is required"
            }), 500
        
        # Re-initialize Vertex AI to ensure it's properly configured
        try:
            vertexai.init(project=project, location=location)
        except Exception as e:
            print(f"Warning: Vertex AI already initialized: {e}")
        
        # Create runner with session and memory services
        # The Runner will use the agents' configured models (which are set to use Vertex AI)
        session_service = InMemorySessionService()
        memory_service = InMemoryMemoryService()
        
        auto_runner = Runner(
            agent=root_agent,
            app_name="agents",
            session_service=session_service,
            memory_service=memory_service,
        )
        print("Auto runner created.")
        print(f"Using Vertex AI with project: {project}, location: {location}")
        
        # Run the agent asynchronously and get the response
        # Use asyncio.run() to execute the async function from sync context
        final_summary = asyncio.run(
            run_session(
                auto_runner,
                session_service,
                prompt,
                app_name="agents",
                user_id="api_user",
                session_id=f"session_{hash(prompt) % 10000}"  # Unique session ID
            )
        )
        
        # Also try to get from session state if available
        # Access the runner's internal session service to get session state
        try:
            # InMemoryRunner has internal session service
            # We can access the last session through the runner
            if hasattr(auto_runner, '_session_service'):
                sessions = auto_runner._session_service.list_sessions()
                if sessions:
                    last_session = sessions[-1]
                    session_summary = last_session.state.get("final_summary", "")
                    if session_summary:
                        final_summary = session_summary
        except Exception as e:
            print(f"Note: Could not access session state: {e}")
        
        # Right after getting final_summary
        print("=" * 80)
        print("RAW SUMMARY OUTPUT:")
        print(final_summary)
        print("=" * 80)

        # Parse the summary into structured data
        structured_data = parse_summary_to_structured_data(final_summary)

        print("=" * 80)
        print("PARSED STRUCTURED DATA:")
        print(json.dumps(structured_data, indent=2))
        print("=" * 80)
        
        # Clean up - InMemoryRunner manages sessions internally
        # Sessions are automatically cleaned up when the runner goes out of scope
        
        return jsonify({
            "success": True,
            "summary": final_summary,
            "structured_data": structured_data
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in plan_meals: {error_details}")
        return jsonify({
            "error": str(e),
            "details": error_details
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

