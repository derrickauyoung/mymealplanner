# Deployment Guide for My Meal Planner

## Google Cloud Deployment

### Prerequisites
1. Google Cloud account with billing enabled
2. Google Cloud SDK installed (`gcloud`)
3. Docker installed (for local testing)
4. Project with Vertex AI API enabled

### Step 1: Set up Google Cloud Project

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Configure Environment Variables

**⚠️ Security Note**: For production, use Google Cloud Secret Manager instead of plain environment variables. See `SECURITY.md` for detailed instructions.

For quick setup, you can use environment variables:
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION`: Region (e.g., `us-central1`)

**Important**: Do NOT hardcode project IDs or sensitive values in `app.yaml`. The file has been updated to remove hardcoded values.

### Step 3: Deploy to Cloud Run

#### Option A: Using Cloud Build (Recommended)

```bash
# Submit build
gcloud builds submit --config cloudbuild.yaml
```

#### Option B: Manual Deployment

```bash
# Build and push image
docker build -t gcr.io/$PROJECT_ID/mymealplanner .
docker push gcr.io/$PROJECT_ID/mymealplanner

# Deploy to Cloud Run
gcloud run deploy mymealplanner \
  --image gcr.io/$PROJECT_ID/mymealplanner \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1
```

### Step 4: Get the Service URL

After deployment, get your service URL:

```bash
gcloud run services describe mymealplanner --region us-central1 --format 'value(status.url)'
```

### Step 5: Update Frontend API URL

Update `index.html` to use your Cloud Run URL:

```javascript
const API_URL = 'https://YOUR_SERVICE_URL/plan';
```

Or set it as an environment variable when serving the page.

## GitHub Pages Deployment

### Step 1: Update API URL in index.html

Before deploying, update the `API_URL` constant in `index.html`:

```javascript
const API_URL = 'https://your-cloud-run-url.run.app/plan';
```

### Step 2: Deploy to GitHub Pages

1. Push your code to GitHub
2. Go to repository Settings > Pages
3. Select source branch (usually `main`)
4. Select `/ (root)` as the folder
5. Save

Your site will be available at: `https://yourusername.github.io/mymealplanner/`

### Step 3: Enable CORS (if needed)

If you encounter CORS issues, ensure your Cloud Run service allows requests from your GitHub Pages domain. The Flask-CORS configuration in `main.py` should handle this, but you may need to update it.

#### NOTE: Cloud Run Service Access

You may still encounter CORS issues if the Google Cloud Run Service is not set to allow unauthenticated requests.

```bash
gcloud run services add-iam-policy-binding mymealplanner \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

To test if public access is enabled:

```bash
curl -I -X OPTIONS https://mymealplanner-${PROJECT_ID}.${CLOUD_LOCATION}.run.app/plan \
  -H "Origin: https://yourusername.github.io" \
  -H "Access-Control-Request-Method: POST"
```

And you should see:

```bash
HTTP/2 204
Access-Control-Allow-Origin: https://derrickauyoung.github.io
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```


## Local Testing

### Test Backend Locally

```bash
# Install dependencies
pip install -r mymealplanner/requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1

# Run the server
python main.py
```

### Test Frontend Locally

Simply open `index.html` in a browser, or use a local server:

```bash
# Python
python -m http.server 8000

# Node.js
npx serve .
```

Then open `http://localhost:8000` in your browser.

## Cost Optimization

- The backend automatically cleans up sessions after processing
- Consider setting Cloud Run concurrency limits
- Use Cloud Run's min instances = 0 to avoid costs when idle
- Monitor usage in Google Cloud Console

## Troubleshooting

### CORS Errors
- Ensure `flask-cors` is installed
- Check that Cloud Run allows your domain

### Agent Errors
- Verify Vertex AI API is enabled
- Check that your project has billing enabled
- Ensure environment variables are set correctly

### Parsing Errors
- The summary parser may need adjustment based on actual agent output
- Check the `parse_summary_to_structured_data` function in `main.py`

