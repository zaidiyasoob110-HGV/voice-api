# 🚀 DEPLOY TO RAILWAY.APP (RECOMMENDED - EASIER THAN RENDER)

## Why Railway Instead of Render?

Railway is **MUCH MORE RELIABLE** for audio processing apps like this:
- ✅ Auto-installs system dependencies
- ✅ Better for librosa/audio libraries
- ✅ Usually works on first try
- ✅ Same free tier as Render
- ✅ Faster deployments

## 3 SIMPLE STEPS

### STEP 1: Upload Files to GitHub

Upload ONLY these 2 files to your GitHub repository:

1. **app.py** (use READY_app.py - rename it)
2. **requirements.txt** (use READY_requirements.txt - rename it)

That's it! Just 2 files needed for Railway.

### STEP 2: Deploy to Railway

1. Go to **https://railway.app**
2. Click **"Start a New Project"**
3. Click **"Deploy from GitHub repo"**
4. Authenticate with GitHub
5. Select your repository
6. Click **Deploy**

**That's it!** Railway will:
- Auto-detect Python
- Install dependencies
- Start your app
- Give you a URL

### STEP 3: Get Your URL

After deployment (2-5 minutes):
1. Click on your deployed service
2. Go to **"Settings"** tab
3. Click **"Generate Domain"** under Networking
4. Copy your URL: `https://your-app.up.railway.app`

## Testing Your Deployment

```bash
# Health check
curl https://your-app.up.railway.app/api/v1/health

# Test detection
curl -X POST "https://your-app.up.railway.app/api/v1/detect-url" \
  -H "Authorization: demo-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://www.kozco.com/tech/piano2.wav",
    "language": "english"
  }'
```

## For Competition Submission

**API Endpoint:**
```
https://your-app.up.railway.app/api/v1/detect-url
```

**API Key:**
```
demo-key-12345
```
(or change it in app.py first)

**Request Format:**
```json
{
  "audio_url": "https://your-audio-file.com/sample.mp3",
  "language": "english"
}
```

## Update API Key (Optional)

Before deploying, edit `app.py` line 24:

```python
VALID_API_KEYS = {
    "your-custom-key-here": "production_user",
}
```

---

# IF YOU STILL WANT TO TRY RENDER

## Files for Render (3 files needed)

1. **app.py** (use READY_app.py)
2. **requirements.txt** (use READY_requirements.txt)
3. **render.yaml** (use READY_render.yaml)

### Render Configuration

In Render dashboard:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Environment:** Python 3

---

# COMPARISON

| Feature | Railway | Render |
|---------|---------|--------|
| Audio libraries | ✅ Easy | ⚠️ Complex |
| Setup | ✅ 1-click | ⚠️ Manual config |
| First-time success | ✅ High | ⚠️ Low |
| Free tier | ✅ 500 hours | ✅ 750 hours |
| Deployment time | ✅ 2-3 min | ⚠️ 5-10 min |

**Recommendation: Use Railway!** 🚀

---

# Files You Need

## For Railway (2 files):
1. READY_app.py → rename to `app.py`
2. READY_requirements.txt → rename to `requirements.txt`

## For Render (3 files):
1. READY_app.py → rename to `app.py`
2. READY_requirements.txt → rename to `requirements.txt`
3. READY_render.yaml → rename to `render.yaml`

---

# Quick Start

```bash
# 1. Download files
# 2. Rename:
mv READY_app.py app.py
mv READY_requirements.txt requirements.txt

# 3. Update API key in app.py (line 24)

# 4. Push to GitHub
git add .
git commit -m "Deploy voice detection API"
git push

# 5. Deploy to Railway.app
# Go to railway.app → Deploy from GitHub repo
```

Done! 🎉
