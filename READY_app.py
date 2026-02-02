from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Literal, Optional
import uvicorn
from datetime import datetime
import logging
import requests
import base64
import io

# Minimal imports - only load heavy libraries when needed
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Voice Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys - CHANGE THESE!
VALID_API_KEYS = {
    "demo-key-12345": "demo_user",
}

class AudioRequestURL(BaseModel):
    audio_url: HttpUrl
    language: Literal["tamil", "english", "hindi", "malayalam", "telugu"]

class AudioRequestBase64(BaseModel):
    audio_base64: str
    language: Literal["tamil", "english", "hindi", "malayalam", "telugu"]

class DetectionResponse(BaseModel):
    status: str
    result: Literal["AI_GENERATED", "HUMAN"]
    confidence: float
    language: str
    timestamp: str
    metadata: dict = {}

def verify_api_key(api_key: str) -> bool:
    return api_key in VALID_API_KEYS

def download_audio(url: str) -> bytes:
    try:
        logger.info(f"Downloading: {url}")
        response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        return response.content
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

def analyze_audio(audio_data: bytes, language: str) -> tuple[str, float]:
    """Simple audio analysis - imports librosa only when needed"""
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(io.BytesIO(audio_data), sr=22050, duration=30)
        
        # Extract basic features
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        rms = librosa.feature.rms(y=y)[0]
        
        # Simple scoring
        score = 0.0
        checks = 0
        
        if np.std(zcr) < 0.02:
            score += 1
        checks += 1
        
        if np.mean(np.std(mfccs, axis=1)) < 15:
            score += 1
        checks += 1
        
        if np.std(rms) < 0.01:
            score += 1
        checks += 1
        
        confidence = score / checks if checks > 0 else 0.5
        
        # Language adjustment
        adj = {'tamil': 0.95, 'english': 1.0, 'hindi': 0.98, 'malayalam': 0.96, 'telugu': 0.97}
        confidence *= adj.get(language, 1.0)
        
        if confidence >= 0.5:
            return "AI_GENERATED", min(confidence, 1.0)
        else:
            return "HUMAN", min(1.0 - confidence, 1.0)
            
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/")
async def root():
    return {
        "service": "AI Voice Detection API",
        "status": "running",
        "endpoints": ["/api/v1/health", "/api/v1/detect-url", "/api/v1/detect"]
    }

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/api/v1/info")
async def info():
    return {
        "name": "AI Voice Detection API",
        "version": "1.0.0",
        "languages": ["tamil", "english", "hindi", "malayalam", "telugu"]
    }

@app.post("/api/v1/detect-url", response_model=DetectionResponse)
async def detect_url(
    request: AudioRequestURL,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    api_key = x_api_key or authorization
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        audio_data = download_audio(str(request.audio_url))
        result, confidence = analyze_audio(audio_data, request.language)
        
        return DetectionResponse(
            status="success",
            result=result,
            confidence=round(confidence, 4),
            language=request.language,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata={
                "audio_size_bytes": len(audio_data),
                "input_type": "url",
                "source_url": str(request.audio_url)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_base64(
    request: AudioRequestBase64,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    api_key = x_api_key or authorization
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        audio_data = base64.b64decode(request.audio_base64)
        result, confidence = analyze_audio(audio_data, request.language)
        
        return DetectionResponse(
            status="success",
            result=result,
            confidence=round(confidence, 4),
            language=request.language,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata={
                "audio_size_bytes": len(audio_data),
                "input_type": "base64"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
