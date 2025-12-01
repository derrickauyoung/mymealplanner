# My Meal Planner

A meal planner using AI agents to do the difficult work of collecting and summarizing a meal plan and ingredients lists.

## Features

- 🤖 Multi-agent AI system using Google's Vertex AI
- 🍽️ Generates 7-day meal plans with breakfast, lunch, and dinner
- 📝 Provides detailed ingredient lists organized by day
- 🔗 Includes clickable recipe links for easy access
- 🎨 Beautiful React-based frontend
- ☁️ Deployed on Google Cloud Run
- 🆓 Free hosting on GitHub Pages

## Architecture

### Backend
- **Google Cloud Run** - Serverless container hosting
- **Flask** - REST API framework
- **Google ADK (Agent Development Kit)** - Multi-agent orchestration
- **Vertex AI** - LLM backend (Gemini models)

### Frontend
- **React** (via CDN) - UI framework
- **GitHub Pages** - Static hosting
- Responsive design with modern UI

## Quick Start

### Prerequisites
- Google Cloud account with billing enabled
- Google Cloud SDK (`gcloud`) installed
- Python 3.9+
- Docker (for local testing)

### Deployment Steps

1. **Set up Google Cloud Project**
   ```bash
   export PROJECT_ID=your-project-id
   gcloud config set project $PROJECT_ID
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   ```

2. **Deploy Backend to Cloud Run**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

3. **Get Your Service URL**
   ```bash
   gcloud run services describe mymealplanner --region us-central1 --format 'value(status.url)'
   ```

4. **Update Frontend API URL**
   - Open `index.html`
   - Update the `API_URL` constant with your Cloud Run URL:
     ```javascript
     const API_URL = 'https://your-service-url.run.app/plan';
     ```

5. **Deploy Frontend to GitHub Pages**
   - Push code to GitHub
   - Go to Settings > Pages
   - Select source branch and root folder
   - Your site will be live at `https://yourusername.github.io/mymealplanner/`

## Local Development

### Quick Start (Recommended)

**Mac/Linux:**
```bash
# Set your Google Cloud project ID
export GOOGLE_CLOUD_PROJECT=your-project-id

# Run the setup and start script
./run_local.sh
```

**Windows:**
```cmd
REM Set your Google Cloud project ID
set GOOGLE_CLOUD_PROJECT=your-project-id

REM Run the setup and start script
run_local.bat
```

The script will:
- Create a virtual environment (if needed)
- Install all dependencies
- Start the backend server on `http://localhost:8080`

### Manual Setup

**Backend:**
```bash
# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r mymealplanner/requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1  # Optional, defaults to us-central1

# Run server
python main.py
```

**Frontend:**
The frontend automatically detects when running on localhost and connects to `http://localhost:8080`.

Simply open `index.html` in your browser, or use a local server:
```bash
# Python
python -m http.server 8000

# Node.js
npx serve .

# Then open http://localhost:8000 in your browser
```

### Testing the Backend

After starting the server, you can test it:

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test meal planning (this will take a few minutes)
python test_local.py
```

Or use the test script:
```bash
python test_local.py
```

## Project Structure

```
mymealplanner/
├── main.py                          # Flask backend
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container definition
├── cloudbuild.yaml                  # Cloud Build config
├── README.md
├── run_local.sh                     # Local testing script (Mac/Linux)
├── run_local.bat                    # Local testing script (Windows)
├── test_local.py                    # Backend test script
└── DEPLOYMENT.md                    # Detailed deployment guide
│
├── mymealplanner/                   # Python package
│   ├── __init__.py
│   ├── agent.py                     # Agent definitions
│   ├── agent_utils.py               # Helper functions
│   └── parsing.py                   # Parsing utilities
│
├── static/                          # Static frontend files
│   ├── css/
│   │   └── styles.css               # Main stylesheet
│   ├── js/
│   │   └── app.js                   # React app
│   └── resources/
│       └── MyMealPlanner.png        # Images
│
└── templates/
    └── index.html                   # HTML template
```

## How It Works

1. **User submits prompt** via the React frontend
2. **Backend receives request** and creates an agent session
3. **Recipe Search Agent** searches for diverse recipes using Google Search
4. **Summarizer Agent** formats the results into a structured meal plan
5. **Web Page Builder Agent** prepares the final output
6. **Backend parses** the summary into structured JSON
7. **Frontend displays** results in three tabs:
   - **Summary**: Meals organized by day
   - **Ingredients**: Shopping lists by day
   - **Recipes**: All recipe links by day
8. **Session cleanup** prevents ongoing resource usage

## Customization

### Changing the Default Prompt
Edit the `useState` in `index.html`:
```javascript
const [prompt, setPrompt] = useState("Your custom prompt here");
```

### Modifying Agent Behavior
Edit `mymealplanner/agent.py` to adjust:
- Recipe search strategies
- Summary formatting
- Agent instructions

## Security

**⚠️ Important**: For production deployments, use Google Cloud Secret Manager for sensitive values instead of hardcoded environment variables.

- See `SECURITY.md` for detailed security setup instructions
- Never commit secrets or credentials to version control
- Use service accounts with least privilege IAM roles
- Enable audit logging for secret access

Quick security checklist:
- ✅ Use Secret Manager for sensitive values
- ✅ Remove hardcoded project IDs from config files
- ✅ Use `.env` files for local development (already in `.gitignore`)
- ✅ Grant minimal IAM permissions to service accounts

## Cost Optimization

- Sessions are automatically cleaned up after processing
- Cloud Run scales to zero when not in use
- Uses efficient Gemini Flash Lite models
- Monitor usage in Google Cloud Console

## Troubleshooting

See `DEPLOYMENT.md` for detailed troubleshooting steps.
See `SECURITY.md` for security-related issues.

## License

See LICENSE file for details.
