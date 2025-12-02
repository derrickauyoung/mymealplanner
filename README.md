# My Meal Planner

## Problem Statement

Every week, my wife spends hours searching and cross-referencing recipe books and google searches to come up with healthy, in-season, kid-friendly, quick, and delicious meals, gather ingredients lists and get it all ready for the supermarket shop for our family. It is all-consuming, and literally a chore for her. I thought to myself - how can I help her lighten the load with what I learned at the 5-Day AI Agents Intensive Course hosted by Kaggle and Google?

## Why agents?

Agents provide a way to delegate and offload a lot of the tedious work required to generate new meal ideas (3 meals a day for 7 days), gather ingredients lists. If successful, this agent will save hours of time each week.

## What's the overall architecture? 

This started out as a multi-agent solution using a memory bank, with:
 - one orchestrator root SequentialAgent that will take the user's prompt, like "Make me an organized meal planner summary for the next 7 days, with the supplied criteria config ("healthy", "in-season", "kid-friendly", "quick", "delicious"), and create a meal plan and ingredients checklist."
- one AgentTool RecipeSearcher agent, which returns a list of 21 recipes for 3 meals a day for the next 7 days, and a list of required ingredients
- one AgentTool Summarizer agent, which takes a list of recipes and ingredients, and returns a report of the meal plan and ingredients list to the root agent

It ended up being a full-stack web application, using python and flask as its back-end, and React for the front-end, served on github pages on my personal github account.

### Backend
- **Google Cloud Run** - Serverless container hosting
- **Flask** - REST API framework
- **Google ADK (Agent Development Kit)** - Multi-agent orchestration
- **Vertex AI** - LLM backend (Gemini models)

### Frontend
- **React** (via CDN) - UI framework
- **GitHub Pages** - Static hosting

I also learned how to use my google cloud account, and set up the right authentication and permissions to provide the live agent service to my app, so my wife can use the app from the convenience of her laptop or phone!

## Demo 

- Run through the kaggle notebook to check out my prototype (https://www.kaggle.com/code/derrickauyoung/mymealplannerassistant)
- Watch the Youtube clip (https://youtu.be/mZZCdhpuhX0)
- Try out the MyMealPlanner web app (https://derrickauyoung.github.io/mymealplanner/)

## The Build -- Tools and/or Technologies Used

### Prototype

This was certainly a journey! I started by prototyping the agent builds and multi-agent orchestration in my Kaggle notebook (linked below).

### Web App

Once I got the Recipe Search Agent prompt and the Summarizer Agent prompt working well enough in the Kaggle notebook, I decided to spend my last day of the competition seeing how quickly I could create a web app with a React front-end to turn this into a functional app for my wife!

With the limited time I had, I created a github repo (derrickauyoung/mymealplanner) and decided to try out the Cursor App for the first time to do a rough first-pass of my web app.

So I gave it this prompt after pushing my first pass agent.py file and splash logo that I created with Canva up to my github repo:

>Can you analyze my multi-agent file in this workspace, set it up to be deployed onto google cloud, and build an index.html in react that can be served on my github as my free "My Meal Planner" landing page? I want to use the provided resources/MyMealPlanner.png as the splash screen, and a pre-filled prompt text box that I can easily modify.

> The initial prompt text should be: "Can you help me come up with a meal plan for the next 7 days with healthy, in-season, kid-friendly, quick, and delicious meals?". There should be one button the user can press after filling in the prompt (or using the default), with the text: "Plan it!", which should run the agent session. After pressing the button, a modal progress bar should display until the processing is complete, and then bring the user to a new page in react which displays the summary information in 3 easy to navigate pages:

> 1. The summary with titles and links to the recipes, separated by days and meals. 

> 2. The ingredients lists with their required quantities, separated by days

> 3. A list of all recipes and their google search links, separated by days for easy reference

> Once processing is complete, be sure to delete any active agents, to prevent incurring google cloud usage costs.

### Cloud Deploy

I then worked with Cursor, Claude, Co-pilot, and Chat-GPT to get my github page fully functional.

This involved setting up my Google Cloud account and Google Cloud Run to deploy agents onto the cloud.

### Auto Deploy and Web Launch

I also set up an automated Github Pages build and deploy workflow to copy my static css, js, png, and index.html files into my website, I finally got the web app up and running, and it's live on the cloud and ready to use!

https://derrickauyoung.github.io/mymealplanner/

## Key Takeaways and Learnings

Some key steps that I discovered along the way were:
- The Agent instructions were crucial to getting back accurate and sensible results, and being more detailed in these string blocks were really helpful in telling it what and what NOT to do
- I tried to get exact links to the recipes themselves, but no matter what I tried, the URLs that the agents provided were all stale or invalid, so I came up with the idea for the app to just provide a google search link with the recipe title, which seems to return the right search result at the top of the list for the most part
- Cursor was a great starting point for connecting the pieces of my agent code and the web app, but it started by dumping all of the files into the root of the repository, so for my own sanity and future maintainability, I decided to ask Claude how to break the files apart into logical directories (py, static, templates). After applying some software surgery, I arrived at the solution now in this repository.
- How to set up my Google Cloud Secret Manager to store my cloud project id and location
- The gcloud and docker commands to deploy my service to Google Cloud Run
- The gcloud command to enable public access to unauthenticated users (accessing the public website)

## TODOs

- Set up the app to add one random day in the second half of the week where you DON'T have to cook (like a cheat day or eat out/to-go day!)
- Learn how to turn this into an mobile app for iPhone/iPad so everyone can save precious time
- Prevent "Event loop is closed" error by refreshing the site properly on subsequent runs

## Features

- 🤖 Multi-agent AI system using Google's Vertex AI
- 🍽️ Generates 7-day meal plans with breakfast, lunch, and dinner
- 📝 Provides interactive ingredient check-lists organized by day
- 🔗 Includes clickable recipe links for easy access
- 🎨 React-based frontend
- ☁️ Deployed on Google Cloud Run
- 🆓 Free hosting on GitHub Pages

## Dev Guide

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
pip install -r requirements.txt

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
