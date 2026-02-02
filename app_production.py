from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator, HttpUrl
import base64
import io
import librosa
import numpy as np
from typing import Literal, Optional
import uvicorn
from datetime import datetime
import logging
import requests
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Voice Detection API",
    description="Detects whether voice samples are AI-generated or human",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys - UPDATE THESE BEFORE DEPLOYMENT
VALID_API_KEYS = {
    "demo-key-12345": "demo_user",
    "test-key-67890": "test_user",
}

class AudioRequestBase64(BaseModel):
    audio_base64: str
    language: Literal["tamil", "english", "hindi", "malayalam", "telugu"]
    
    @validator('audio_base64')
    def validate_base64(cls, v):
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid base64 encoding")

class AudioRequestURL(BaseModel):
    audio_url: HttpUrl
    language: Literal["tamil", "english", "hindi", "malayalam", "telugu"]

class DetectionResponse(BaseModel):
    status: str
    result: Literal["AI_GENERATED", "HUMAN"]
    confidence: float
    language: str
    timestamp: str
    metadata: dict = {}

def verify_api_key(api_key: str) -> bool:
    """Verify API key"""
    return api_key in VALID_API_KEYS

def download_audio_from_url(url: str, timeout: int = 30) -> bytes:
    """Download audio file from URL"""
    try:
        logger.info(f"Downloading audio from: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=timeout, headers=headers, stream=True)
        response.raise_for_status()
        
        audio_data = response.content
        logger.info(f"Downloaded {len(audio_data)} bytes")
        
        if len(audio_data) == 0:
            raise ValueError("Downloaded file is empty")
        
        return audio_data
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout while downloading audio")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download audio: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading audio: {str(e)}")

def extract_audio_features(audio_data: bytes) -> dict:
    """Extract audio features with error handling"""
    try:
        # Load audio
        audio_buffer = io.BytesIO(audio_data)
        y, sr = librosa.load(audio_buffer, sr=22050, duration=30)  # Limit to 30 seconds
        
        if len(y) == 0:
            raise ValueError("Audio data is empty")
        
        features = {}
        
        # Spectral features
        try:
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid_mean'] = float(np.mean(spec_cent))
            features['spectral_centroid_std'] = float(np.std(spec_cent))
        except Exception as e:
            logger.warning(f"Spectral centroid error: {e}")
            features['spectral_centroid_mean'] = 0.0
            features['spectral_centroid_std'] = 0.0
        
        try:
            spec_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['spectral_rolloff_mean'] = float(np.mean(spec_rolloff))
        except Exception as e:
            logger.warning(f"Spectral rolloff error: {e}")
            features['spectral_rolloff_mean'] = 0.0
        
        try:
            spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            features['spectral_bandwidth_mean'] = float(np.mean(spec_bw))
        except Exception as e:
            logger.warning(f"Spectral bandwidth error: {e}")
            features['spectral_bandwidth_mean'] = 0.0
        
        # MFCC
        try:
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = [float(x) for x in np.mean(mfccs, axis=1)]
            features['mfcc_std'] = [float(x) for x in np.std(mfccs, axis=1)]
        except Exception as e:
            logger.warning(f"MFCC error: {e}")
            features['mfcc_mean'] = [0.0] * 13
            features['mfcc_std'] = [0.0] * 13
        
        # ZCR
        try:
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zcr_mean'] = float(np.mean(zcr))
            features['zcr_std'] = float(np.std(zcr))
        except Exception as e:
            logger.warning(f"ZCR error: {e}")
            features['zcr_mean'] = 0.0
            features['zcr_std'] = 0.0
        
        # RMS
        try:
            rms = librosa.feature.rms(y=y)[0]
            features['rms_mean'] = float(np.mean(rms))
            features['rms_std'] = float(np.std(rms))
        except Exception as e:
            logger.warning(f"RMS error: {e}")
            features['rms_mean'] = 0.0
            features['rms_std'] = 0.0
        
        # Pitch
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(min(pitches.shape[1], 100)):  # Limit iterations
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                features['pitch_mean'] = float(np.mean(pitch_values))
                features['pitch_std'] = float(np.std(pitch_values))
                features['pitch_range'] = float(max(pitch_values) - min(pitch_values))
            else:
                features['pitch_mean'] = 0.0
                features['pitch_std'] = 0.0
                features['pitch_range'] = 0.0
        except Exception as e:
            logger.warning(f"Pitch error: {e}")
            features['pitch_mean'] = 0.0
            features['pitch_std'] = 0.0
            features['pitch_range'] = 0.0
        
        return features
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

def detect_ai_voice(features: dict, language: str) -> tuple[str, float]:
    """Detect AI voice based on features"""
    
    ai_score = 0.0
    total_checks = 0
    
    # Spectral consistency
    if features.get('spectral_centroid_std', 0) < 200:
        ai_score += 1
    total_checks += 1
    
    # MFCC variance
    mfcc_std_avg = np.mean(features.get('mfcc_std', [0]))
    if mfcc_std_avg < 15:
        ai_score += 1
    total_checks += 1
    
    # ZCR consistency
    if features.get('zcr_std', 0) < 0.02:
        ai_score += 1
    total_checks += 1
    
    # Pitch consistency
    if features.get('pitch_std', 0) < 20 and features.get('pitch_mean', 0) > 0:
        ai_score += 1
    total_checks += 1
    
    # RMS consistency
    if features.get('rms_std', 0) < 0.01:
        ai_score += 0.5
    total_checks += 1
    
    # Pitch range
    if features.get('pitch_range', 0) < 50 and features.get('pitch_mean', 0) > 0:
        ai_score += 0.5
    total_checks += 1
    
    # Calculate confidence
    raw_confidence = ai_score / total_checks if total_checks > 0 else 0.5
    
    # Language adjustment
    language_factors = {
        'tamil': 0.95,
        'english': 1.0,
        'hindi': 0.98,
        'malayalam': 0.96,
        'telugu': 0.97
    }
    
    adjusted_confidence = raw_confidence * language_factors.get(language, 1.0)
    
    # Classification
    threshold = 0.5
    if adjusted_confidence >= threshold:
        result = "AI_GENERATED"
        confidence = min(adjusted_confidence, 1.0)
    else:
        result = "HUMAN"
        confidence = min(1.0 - adjusted_confidence, 1.0)
    
    confidence = max(0.0, min(1.0, confidence))
    return result, round(confidence, 4)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Voice Detection API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "info": "/api/v1/info",
            "detect_base64": "/api/v1/detect",
            "detect_url": "/api/v1/detect-url"
        }
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }

@app.get("/api/v1/info")
async def api_info():
    """API information"""
    return {
        "name": "AI Voice Detection API",
        "version": "1.0.0",
        "supported_languages": ["tamil", "english", "hindi", "malayalam", "telugu"],
        "endpoints": ["/api/v1/detect", "/api/v1/detect-url", "/api/v1/health", "/api/v1/info"],
        "input_formats": ["base64", "url"]
    }

@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_voice_base64(
    request: AudioRequestBase64,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Detect voice from base64 audio"""
    
    api_key = x_api_key or authorization
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    try:
        audio_data = base64.b64decode(request.audio_base64)
        features = extract_audio_features(audio_data)
        result, confidence = detect_ai_voice(features, request.language)
        
        return DetectionResponse(
            status="success",
            result=result,
            confidence=confidence,
            language=request.language,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata={
                "audio_size_bytes": len(audio_data),
                "features_extracted": len(features),
                "model_version": "1.0.0",
                "input_type": "base64"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/detect-url", response_model=DetectionResponse)
async def detect_voice_url(
    request: AudioRequestURL,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Detect voice from audio URL"""
    
    api_key = x_api_key or authorization
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    try:
        audio_data = download_audio_from_url(str(request.audio_url))
        features = extract_audio_features(audio_data)
        result, confidence = detect_ai_voice(features, request.language)
        
        return DetectionResponse(
            status="success",
            result=result,
            confidence=confidence,
            language=request.language,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata={
                "audio_size_bytes": len(audio_data),
                "features_extracted": len(features),
                "model_version": "1.0.0",
                "input_type": "url",
                "source_url": str(request.audio_url)
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
