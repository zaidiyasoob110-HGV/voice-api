# Fixed Deployment Guide for Render.com

## The Problem

Your deployment failed with "Exited with status 2" because:
1. Missing system dependencies (libsndfile1, ffmpeg)
2. Incorrect build configuration
3. Python version compatibility issues

## The Solution

I've created fixed files that will work on Render.com:

### ✅ Files to Upload to Your GitHub Repository

1. **app.py** (rename app_production.py to app.py)
2. **requirements.txt** (use requirements_fixed.txt)
3. **build.sh** (new file - build script)
4. **runtime.txt** (new file - Python version)
5. **apt-packages** (new file - system dependencies)
6. **render.yaml** (optional - deployment config)

## Step-by-Step Fix

### Option 1: Using Render Dashboard (EASIEST)

1. **Go to your Render dashboard**
2. **Delete the current failing service** (if exists)
3. **Update your GitHub repository** with the new files:
   ```bash
   # Copy these files to your repo:
   - app_production.py → rename to app.py
   - requirements_fixed.txt → rename to requirements.txt
   - build.sh (new)
   - runtime.txt (new)
   - apt-packages (new)
   ```

4. **Create new Web Service on Render:**
   - Connect your GitHub repo
   - **Build Command:** `./build.sh`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment:** Python 3

5. **Make build.sh executable** (add this to your repo):
   ```bash
   chmod +x build.sh
   ```

### Option 2: Manual Configuration (if build.sh doesn't work)

If the build script fails, use this **Build Command** directly in Render:

```bash
pip install --upgrade pip && pip install -r requirements.txt
```

**Note:** Render's Python environment on free tier comes with `libsndfile1` and `ffmpeg` pre-installed, so we don't need to install them manually in most cases.

### Option 3: Use render.yaml (RECOMMENDED)

1. Add `render.yaml` to your repository root
2. Render will auto-detect and use this configuration
3. This file includes all necessary build steps

## Updated File Contents

### 1. requirements.txt (requirements_fixed.txt)
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

### 2. build.sh
```bash
#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. runtime.txt
```
python-3.10.13
```

### 4. apt-packages
```
libsndfile1
ffmpeg
```

### 5. app.py (app_production.py)
- Production-ready with better error handling
- CORS enabled
- Both /detect and /detect-url endpoints
- Improved logging

## Testing After Deployment

Once deployed, test with:

```bash
# Health check
curl https://your-app.onrender.com/api/v1/health

# Test with URL
curl -X POST "https://your-app.onrender.com/api/v1/detect-url" \
  -H "Authorization: demo-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://example.com/test.mp3",
    "language": "english"
  }'
```

## Important Notes

### 1. Update API Keys
Before deploying, update the API keys in `app.py`:

```python
VALID_API_KEYS = {
    "your-secure-key-here": "production_user",
}
```

### 2. Build Time
First deployment takes 5-10 minutes (installing librosa and dependencies)

### 3. Free Tier Limitations
- Will spin down after inactivity
- First request after spin-down takes 50+ seconds
- Consider upgrading for production use

## Troubleshooting

### If build still fails:

1. **Check Python version:**
   - Ensure runtime.txt has `python-3.10.13`

2. **Simplify requirements:**
   - Remove version numbers if conflicts occur
   - Try: `librosa` instead of `librosa==0.10.1`

3. **Check logs:**
   - Go to Render dashboard → Logs
   - Look for specific error messages

4. **Try minimal requirements first:**
   ```
   fastapi
   uvicorn[standard]
   pydantic
   librosa
   requests
   ```

### If app starts but crashes:

1. **Check memory usage:**
   - Free tier has 512MB RAM
   - librosa can be memory-intensive
   - Solution: Limit audio duration in code (already done - 30 seconds max)

2. **Check environment variables:**
   - PORT is automatically set by Render
   - No need to set manually

## Alternative: Deploy to Railway.app

If Render continues to fail, try Railway.app:

1. Push code to GitHub
2. Go to railway.app
3. "New Project" → "Deploy from GitHub"
4. Select your repository
5. Railway auto-detects Python and installs dependencies
6. Done! (Usually works on first try)

Railway is often more reliable for audio processing apps.

## What to Submit to Competition

Once deployed successfully:

**API Endpoint URL:**
```
https://your-app.onrender.com/api/v1/detect-url
```

**API Key:**
```
demo-key-12345
```
(or your custom key)

**Supported Languages:**
- tamil
- english  
- hindi
- malayalam
- telugu

**Request Format:**
```json
{
  "audio_url": "https://your-audio-url.com/sample.mp3",
  "language": "english"
}
```

## Quick Deploy Checklist

- [ ] Update API keys in app_production.py
- [ ] Rename app_production.py to app.py
- [ ] Rename requirements_fixed.txt to requirements.txt
- [ ] Add build.sh, runtime.txt, apt-packages to repo
- [ ] Make build.sh executable (`chmod +x build.sh`)
- [ ] Push to GitHub
- [ ] Create new Render service
- [ ] Set build command: `./build.sh`
- [ ] Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- [ ] Wait for deployment (5-10 minutes)
- [ ] Test with curl
- [ ] Submit to competition

Good luck! 🚀
