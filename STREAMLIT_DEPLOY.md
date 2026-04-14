Streamlit Community Cloud Deployment Steps
-------------------------------------------

Prerequisites:
  - The FastAPI backend must already be deployed and publicly accessible.
    Get its URL from Railway: railway domain
  - Your code must be pushed to a public GitHub repository.

Steps:

1. Go to https://share.streamlit.io and sign in with GitHub.

2. Click "New app".

3. Fill in:
     Repository: your-github-username/rag-pipeline
     Branch:     main
     Main file:  ui/Home.py

4. Click "Advanced settings" and set Secrets:
     API_BASE_URL = "https://your-railway-url.up.railway.app"

5. Click "Deploy". Streamlit will install requirements from ui/requirements.txt
   and start the app. This takes 2-3 minutes on first deploy.

6. Your public URL will be:
     https://your-username-rag-pipeline-home-xxxx.streamlit.app

7. Test the deployed UI:
     - Open the URL in a browser.
     - Go to Home page and verify "Backend is online" message appears.
     - Upload a test document on the Upload Documents page.
     - Ask a question on the Ask Questions page.

Redeployment:
  Push a commit to main. Streamlit Cloud automatically redeploys within 1-2 minutes.

Troubleshooting:
  - "Cannot connect to backend": Verify API_BASE_URL in secrets is correct.
  - "Module not found": Check ui/requirements.txt has all needed packages.
  - CORS errors: The FastAPI backend uses allow_origins=["*"] so this should not occur.
