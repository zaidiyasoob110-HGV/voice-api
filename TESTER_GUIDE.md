# Endpoint Tester Guide - For Competition Submission

## What the Tester Expects

Based on the endpoint tester interface, you need to provide:

1. **API Endpoint URL** - Your deployed endpoint URL
2. **Authorization/API Key** - In the header
3. **Short message** - Test request description (optional)
4. **Audio file URL** - A publicly accessible MP3 file URL

## Updated API Information

### NEW: URL-Based Endpoint

**Endpoint:** `/api/v1/detect-url`

**Method:** POST

**Headers:**
```
Authorization: your-api-key-here
```
or
```
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "audio_url": "https://example.com/sample.mp3",
  "language": "english"
}
```

**Response:**
```json
{
  "status": "success",
  "result": "AI_GENERATED",
  "confidence": 0.8542,
  "language": "english",
  "timestamp": "2024-02-02T10:30:45.123456Z",
  "metadata": {
    "audio_size_bytes": 245760,
    "features_extracted": 25,
    "model_version": "1.0.0",
    "input_type": "url",
    "source_url": "https://example.com/sample.mp3"
  }
}
```

## How to Fill the Endpoint Tester

### 1. API Endpoint URL
```
https://your-deployment-url.com/api/v1/detect-url
```

### 2. Authorization / API Key
In the header field, enter:
```
your-api-key-here
```

The API accepts the key in either:
- `Authorization` header
- `X-API-Key` header

### 3. Short Message (Optional)
```
Testing AI voice detection for English sample
```

### 4. Audio File URL
You need a **publicly accessible MP3 file URL**. Options:

**Option A: Use Google Drive (Make Public)**
1. Upload MP3 to Google Drive
2. Right-click → Share → Change to "Anyone with the link"
3. Get the file ID from the share link
4. Use this format:
```
https://drive.google.com/uc?export=download&id=YOUR_FILE_ID
```

**Option B: Use Dropbox**
1. Upload MP3 to Dropbox
2. Get share link
3. Change `www.dropbox.com` to `dl.dropboxusercontent.com`
4. Change `?dl=0` to `?dl=1`

**Option C: Use a File Hosting Service**
- filetransfer.io
- tmpfiles.org
- file.io
- Any public URL pointing to an MP3 file

### 5. Language
The request body should include:
```json
{
  "audio_url": "your-public-mp3-url",
  "language": "english"
}
```

Supported languages:
- `tamil`
- `english`
- `hindi`
- `malayalam`
- `telugu`

## Complete Example for Tester

**API Endpoint URL:**
```
https://your-app.onrender.com/api/v1/detect-url
```

**Authorization:**
```
your-api-key-here
```

**Message:**
```
Test request for English voice sample
```

**Request Body (what the tester will send):**
```json
{
  "audio_url": "https://drive.google.com/uc?export=download&id=1AbCdEfGhIjK",
  "language": "english"
}
```

## Testing Before Submission

### Test with cURL:
```bash
curl -X POST "https://your-app.onrender.com/api/v1/detect-url" \
  -H "Authorization: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://your-public-mp3-url.com/sample.mp3",
    "language": "english"
  }'
```

### Test with Python:
```python
import requests

response = requests.post(
    'https://your-app.onrender.com/api/v1/detect-url',
    headers={
        'Authorization': 'your-api-key-here',
        'Content-Type': 'application/json'
    },
    json={
        'audio_url': 'https://your-public-mp3-url.com/sample.mp3',
        'language': 'english'
    }
)

print(response.json())
```

## Updated Deployment Steps

### 1. Use the New File
Replace `app.py` with `app_with_url.py`:

```bash
# Rename the file
mv app_with_url.py app.py
```

Or update your deployment to use `app_with_url.py` directly.

### 2. Update requirements.txt
Make sure it includes:
```
requests==2.31.0
```

### 3. Deploy to Your Platform

**Render.com:**
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`

**Railway:**
- Auto-detects and deploys

**Docker:**
```bash
docker build -t ai-voice-detection .
docker run -p 8000:8000 ai-voice-detection
```

### 4. Update API Key
In `app_with_url.py`, update:
```python
VALID_API_KEYS = {
    "your-production-api-key": "production_user",
}
```

### 5. Test Your Deployed Endpoint

```bash
# Health check
curl https://your-app.onrender.com/api/v1/health

# Test with URL
curl -X POST "https://your-app.onrender.com/api/v1/detect-url" \
  -H "Authorization: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"audio_url": "https://example.com/test.mp3", "language": "english"}'
```

## What to Submit

1. **Deployed API URL:**
   ```
   https://your-app.onrender.com/api/v1/detect-url
   ```

2. **API Key:**
   ```
   your-production-api-key
   ```

3. **Supported Languages:**
   - tamil
   - english
   - hindi
   - malayalam
   - telugu

4. **Input Format:**
   - Method: POST
   - Headers: Authorization or X-API-Key
   - Body: JSON with `audio_url` and `language`

## Troubleshooting

### "Failed to download audio"
- Ensure the URL is publicly accessible
- Check if the URL points directly to the MP3 file
- Test the URL in a browser first

### "Invalid API key"
- Verify the key matches what's in your deployed code
- Check header name (Authorization or X-API-Key)

### "Request timeout"
- Audio file might be too large
- Check your server is running
- Verify network connectivity

## Both Endpoints Available

Your API now supports BOTH input methods:

1. **Base64 Input:** `/api/v1/detect` (original)
2. **URL Input:** `/api/v1/detect-url` (for tester)

Use `/api/v1/detect-url` for the competition tester!
