# 🔧 STEP-BY-STEP FIX GUIDE

## Your Problem
❌ Render deployment failed with "Exited with status 2 while building your code"

## The Fix (3 Simple Steps)

### STEP 1: Update Your GitHub Repository

Replace these files in your repository:

1. **app.py** ← Use **app_production.py** (rename it)
2. **requirements.txt** ← Use **requirements_fixed.txt** (rename it)

Add these NEW files to your repository:

3. **build.sh** (new file)
4. **runtime.txt** (new file)
5. **apt-packages** (new file)
6. **render.yaml** (optional but recommended)

### STEP 2: Make build.sh Executable

In your repository, run:
```bash
chmod +x build.sh
```

Or add this to your GitHub Actions / commit:
```bash
git add build.sh
git update-index --chmod=+x build.sh
git commit -m "Make build.sh executable"
git push
```

### STEP 3: Redeploy on Render

**Option A: Using render.yaml (EASIEST)**
1. Just push the files to GitHub
2. Render will auto-detect render.yaml and configure everything
3. Done!

**Option B: Manual Configuration**
1. Go to your Render dashboard
2. Delete the failing service (if exists)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name:** voice-api
   - **Environment:** Python 3
   - **Build Command:** `./build.sh`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"

## File Contents Summary

### ✅ app_production.py (rename to app.py)
- Production-ready with better error handling
- Both /detect and /detect-url endpoints
- CORS enabled
- Improved logging
- **ACTION:** Update API keys before deployment!

### ✅ requirements_fixed.txt (rename to requirements.txt)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.4.2
librosa==0.10.1
numpy==1.24.3
soundfile==0.12.1
requests==2.31.0
scipy==1.11.3
numba==0.58.1
```

### ✅ build.sh
```bash
#!/usr/bin/env bash
set -o errexit
pip install --upgrade pip
pip install -r requirements.txt
```

### ✅ runtime.txt
```
python-3.10.13
```

### ✅ apt-packages
```
libsndfile1
ffmpeg
```

### ✅ render.yaml (optional)
```yaml
services:
  - type: web
    name: voice-api
    env: python
    buildCommand: ./build.sh
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Important: Update API Keys

In **app_production.py**, line ~40, change:
```python
VALID_API_KEYS = {
    "demo-key-12345": "demo_user",
    "test-key-67890": "test_user",
}
```

To your own secure keys:
```python
VALID_API_KEYS = {
    "your-production-key-here": "production_user",
}
```

## What Happens After Deployment

1. ⏳ **Build starts** (5-10 minutes - installing dependencies)
2. ✅ **Build succeeds** (you'll see logs showing pip installing packages)
3. 🚀 **App starts** (you'll see "Application startup complete")
4. 🌐 **URL becomes live** (e.g., https://voice-api-xyz.onrender.com)

## Testing Your Deployment

### 1. Health Check
```bash
curl https://your-app.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-02T11:30:00.000000Z",
  "version": "1.0.0"
}
```

### 2. Test Detection (URL)
```bash
curl -X POST "https://your-app.onrender.com/api/v1/detect-url" \
  -H "Authorization: demo-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://www.kozco.com/tech/piano2.wav",
    "language": "english"
  }'
```

### 3. Test Detection (Base64)
```bash
# Encode a small audio file
BASE64_AUDIO=$(base64 -w 0 sample.mp3)

curl -X POST "https://your-app.onrender.com/api/v1/detect" \
  -H "Authorization: demo-key-12345" \
  -H "Content-Type: application/json" \
  -d "{
    \"audio_base64\": \"$BASE64_AUDIO\",
    \"language\": \"english\"
  }"
```

## For the Competition Endpoint Tester

Once deployed successfully, use:

**API Endpoint URL:**
```
https://your-app.onrender.com/api/v1/detect-url
```

**Authorization Header:**
```
your-production-key-here
```

**Audio URL:**
(Any publicly accessible MP3 file URL)
```
https://your-audio-url.com/sample.mp3
```

**Request Body:**
```json
{
  "audio_url": "https://your-audio-url.com/sample.mp3",
  "language": "english"
}
```

## Troubleshooting

### ❌ Build still fails?

1. **Check the logs** in Render dashboard
2. **Look for specific error** (e.g., "No module named X")
3. **Try simpler requirements:**
   ```
   fastapi
   uvicorn[standard]
   librosa
   requests
   ```

### ❌ App starts but crashes?

1. **Memory issue:** Free tier has 512MB RAM
   - Solution already implemented: Audio limited to 30 seconds
2. **Check logs** for specific error
3. **Test locally first:**
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

### ✅ Alternative: Use Railway.app

If Render keeps failing:

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-configures everything
6. Usually works first try!

Railway often handles audio processing libraries better than Render's free tier.

## Quick Checklist

Before deploying:
- [ ] Renamed app_production.py → app.py
- [ ] Renamed requirements_fixed.txt → requirements.txt
- [ ] Added build.sh
- [ ] Added runtime.txt
- [ ] Added apt-packages
- [ ] Added render.yaml (optional)
- [ ] Made build.sh executable
- [ ] Updated API keys in app.py
- [ ] Pushed all files to GitHub
- [ ] Created/updated Render service
- [ ] Waiting for deployment...

After deployment:
- [ ] Tested health endpoint
- [ ] Tested detect-url endpoint
- [ ] Got successful response
- [ ] Ready to submit to competition!

## Files You Need

All fixed files are in your outputs folder:
1. app_production.py → **rename to app.py**
2. requirements_fixed.txt → **rename to requirements.txt**
3. build.sh
4. runtime.txt
5. apt-packages
6. render.yaml

Copy these to your GitHub repository and deploy!

---

**Need more help?** Check DEPLOYMENT_FIX.md for detailed troubleshooting.

Good luck! 🚀
