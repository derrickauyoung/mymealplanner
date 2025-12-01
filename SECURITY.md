# Security Guide for My Meal Planner

This guide covers security best practices for deploying and running My Meal Planner.

## Using Google Cloud Secret Manager

For production deployments, sensitive values should be stored in Google Cloud Secret Manager rather than hardcoded or passed as plain environment variables.

### Step 1: Create Secrets in Secret Manager

```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Create secret for project ID (if you want to store it as a secret)
echo -n "$PROJECT_ID" | gcloud secrets create mymealplanner-project-id \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID

# Create secret for location (optional, less sensitive)
echo -n "us-central1" | gcloud secrets create mymealplanner-location \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$PROJECT_ID
```

### Step 2: Grant Cloud Run Access to Secrets

```bash
# Get the Cloud Run service account
export SERVICE_ACCOUNT=$(gcloud run services describe mymealplanner \
  --region us-central1 \
  --format 'value(spec.template.spec.serviceAccountName)')

# If no custom service account, use the default
if [ -z "$SERVICE_ACCOUNT" ]; then
  export SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
  export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format 'value(projectNumber)')
fi

# Grant secret accessor role
gcloud secrets add-iam-policy-binding mymealplanner-project-id \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding mymealplanner-location \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project=$PROJECT_ID
```

### Step 3: Update Cloud Run Deployment

Update `cloudbuild.yaml` to use secrets:

```yaml
- name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
  entrypoint: gcloud
  args:
    - 'run'
    - 'deploy'
    - 'mymealplanner'
    - '--image'
    - 'gcr.io/$PROJECT_ID/mymealplanner'
    - '--region'
    - 'us-central1'
    - '--update-secrets'
    - 'GOOGLE_CLOUD_PROJECT=mymealplanner-project-id:latest,GOOGLE_CLOUD_LOCATION=mymealplanner-location:latest'
```

### Alternative: Use Build-Time Substitutions

For non-sensitive values like project ID (which is often public), you can use Cloud Build substitutions:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions _PROJECT_ID=$PROJECT_ID,_LOCATION=us-central1
```

## Security Best Practices

### 1. Never Commit Secrets

- ✅ **DO**: Use Secret Manager for sensitive values
- ✅ **DO**: Use environment variables for local development
- ❌ **DON'T**: Commit secrets to version control
- ❌ **DON'T**: Hardcode credentials in code

### 2. Use Least Privilege IAM

Grant only the minimum permissions needed:

```bash
# Grant Cloud Run service account only necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"
```

### 3. Enable Audit Logging

Monitor access to your secrets:

```bash
# Enable audit logging for Secret Manager
gcloud logging sinks create secret-manager-audit \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/audit_logs \
  --log-filter='protoPayload.serviceName="secretmanager.googleapis.com"'
```

### 4. Rotate Secrets Regularly

```bash
# Create a new version of a secret
echo -n "new-value" | gcloud secrets versions add mymealplanner-project-id \
  --data-file=-
```

### 5. Use Service Accounts

Never use user credentials in production:

```bash
# Create a dedicated service account for Cloud Run
gcloud iam service-accounts create mymealplanner-sa \
  --display-name="My Meal Planner Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:mymealplanner-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## Local Development Security

For local development, use environment variables (never commit `.env` files):

```bash
# Create .env file (add to .gitignore)
cat > .env << EOF
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
EOF

# Load in your shell
export $(cat .env | xargs)
```

## Checking Current Configuration

```bash
# List all secrets
gcloud secrets list --project=$PROJECT_ID

# Check Cloud Run environment variables
gcloud run services describe mymealplanner \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"

# Check IAM bindings for secrets
gcloud secrets get-iam-policy mymealplanner-project-id
```

## Troubleshooting

### Secret Access Denied

If you get permission errors:

```bash
# Verify service account has access
gcloud secrets get-iam-policy mymealplanner-project-id

# Re-grant access if needed
gcloud secrets add-iam-policy-binding mymealplanner-project-id \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

### Secrets Not Found

Ensure secrets exist and are in the correct project:

```bash
# List secrets
gcloud secrets list

# Check secret exists
gcloud secrets describe mymealplanner-project-id
```

## Additional Resources

- [Google Cloud Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Cloud Run Security Best Practices](https://cloud.google.com/run/docs/securing/service-identity)
- [IAM Best Practices](https://cloud.google.com/iam/docs/using-iam-securely)

