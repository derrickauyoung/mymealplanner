# Local Testing Guide

This guide will help you set up and test My Meal Planner locally on your machine.

## Prerequisites

1. **Python 3.9+** installed
2. **Google Cloud Project** with:
   - Vertex AI API enabled
   - Billing enabled
   - Authentication configured (see below)

## Authentication Setup

Before running locally, you need to authenticate with Google Cloud:

```bash
# Install Google Cloud SDK if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Set application default credentials
gcloud auth application-default login
```

## Quick Start

### Option 1: Using the Scripts (Easiest)

**Mac/Linux:**
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
./run_local.sh
```

**Windows:**
```cmd
set GOOGLE_CLOUD_PROJECT=your-project-id
run_local.bat
```

### Option 2: Manual Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r mymealplanner/requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_CLOUD_LOCATION=us-central1  # Optional
   ```

4. **Start the server:**
   ```bash
   python main.py
   ```

   You should see:
   ```
   ✅ recipe_search_agent created.
   ✅ summarizer_agent created.
   ✅ web_page_builder_agent created.
   ✅ root_agent created.
   * Running on http://0.0.0.0:8080
   ```

## Testing the Backend

### Test 1: Health Check

In a new terminal:
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test 2: Full Meal Plan Test

Run the test script:
```bash
python test_local.py
```

Or test manually:
```bash
curl -X POST http://localhost:8080/plan \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a 2-day meal plan with simple recipes."}'
```

**Note:** The first request may take 2-5 minutes as the agents process the request.

## Running the Frontend

### Option 1: Direct File Open

Simply open `index.html` in your browser. The frontend will automatically detect localhost and connect to `http://localhost:8080`.

### Option 2: Local Server (Recommended)

**Python:**
```bash
python -m http.server 8000
```

**Node.js:**
```bash
npx serve .
```

Then open `http://localhost:8000` in your browser.

## Troubleshooting

### Issue: "GOOGLE_CLOUD_PROJECT not set"

**Solution:**
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### Issue: "Authentication Error" or "Permission Denied"

**Solution:**
```bash
# Re-authenticate
gcloud auth application-default login

# Verify project
gcloud config get-value project
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r mymealplanner/requirements.txt
```

### Issue: CORS errors in browser

**Solution:**
The Flask app already has CORS enabled. If you still see errors:
- Make sure you're accessing via `http://localhost` (not `file://`)
- Check that the backend is running on port 8080
- Verify `flask-cors` is installed

### Issue: "Connection refused" when testing

**Solution:**
- Verify the backend is running: `curl http://localhost:8080/health`
- Check the port isn't already in use
- Make sure firewall isn't blocking the connection

### Issue: Agent requests timing out

**Solution:**
- This is normal for the first request (can take 2-5 minutes)
- Check your Google Cloud quota limits
- Verify Vertex AI API is enabled
- Check billing is enabled on your project

## Development Tips

1. **Hot Reload:** The Flask server runs in debug mode, so it will reload on code changes.

2. **Logs:** Check the terminal running `main.py` for detailed logs and errors.

3. **API Testing:** Use tools like Postman or curl to test the API directly.

4. **Frontend Changes:** Refresh the browser to see changes to `index.html`.

5. **Environment Variables:** You can create a `.env` file (not committed) for local development:
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   ```

## Next Steps

Once local testing works:
1. Test with different prompts
2. Verify the parsing works correctly
3. Check that all three tabs (Summary, Ingredients, Recipes) display properly
4. Deploy to Google Cloud Run when ready

## Cost Considerations

- Local testing uses your Google Cloud project's Vertex AI quota
- Each meal plan request uses API calls (charged per use)
- Sessions are automatically cleaned up after each request
- Monitor usage in Google Cloud Console

