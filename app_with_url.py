from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator, HttpUrl
import base64
import io
import librosa
import numpy as np
from typing import Literal, Optional
import uvicorn
from datetime import datetime
import logging
import hashlib
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Voice Detection API",
    description="Detects whether voice samples are AI-generated or human",
    version="1.0.0"
)

# API Key for authentication (in production, use environment variables)
VALID_API_KEYS = {
    "your-api-key-here": "default_user",
}

class AudioRequestBase64(BaseModel):
    """Request model for base64 audio input"""
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
    """Request model for URL-based audio input"""
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
    """Verify if the provided API key is valid"""
    return api_key in VALID_API_KEYS

def download_audio_from_url(url: str, timeout: int = 30) -> bytes:
    """Download audio file from URL"""
    try:
        logger.info(f"Downloading audio from URL: {url}")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        
        # Check if content type is audio
        content_type = response.headers.get('content-type', '')
        if 'audio' not in content_type and not url.endswith('.mp3'):
            logger.warning(f"Content type is {content_type}, proceeding anyway")
        
        audio_data = response.content
        logger.info(f"Downloaded {len(audio_data)} bytes")
        return audio_data
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=408, detail="Request timeout while downloading audio")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download audio: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading audio: {str(e)}")

def extract_audio_features(audio_data: bytes) -> dict:
    """Extract comprehensive audio features for AI detection"""
    try:
        # Load audio from bytes
        audio_buffer = io.BytesIO(audio_data)
        y, sr = librosa.load(audio_buffer, sr=None)
        
        features = {}
        
        # 1. Spectral Features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
        
        features['spectral_centroid_mean'] = float(np.mean(spectral_centroids))
        features['spectral_centroid_std'] = float(np.std(spectral_centroids))
        features['spectral_rolloff_mean'] = float(np.mean(spectral_rolloff))
        features['spectral_bandwidth_mean'] = float(np.mean(spectral_bandwidth))
        features['spectral_contrast_mean'] = float(np.mean(spectral_contrast))
        
        # 2. MFCC Features (crucial for voice analysis)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        features['mfcc_mean'] = [float(x) for x in np.mean(mfccs, axis=1)]
        features['mfcc_std'] = [float(x) for x in np.std(mfccs, axis=1)]
        
        # 3. Zero Crossing Rate (naturalness indicator)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        features['zcr_mean'] = float(np.mean(zcr))
        features['zcr_std'] = float(np.std(zcr))
        
        # 4. Pitch and Harmonics
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
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
        
        # 5. Energy and RMS
        rms = librosa.feature.rms(y=y)[0]
        features['rms_mean'] = float(np.mean(rms))
        features['rms_std'] = float(np.std(rms))
        
        # 6. Temporal Features
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        features['onset_strength_mean'] = float(np.mean(onset_env))
        
        # 7. Chroma Features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features['chroma_mean'] = float(np.mean(chroma))
        
        # 8. Spectral Flatness (AI voices tend to have different flatness)
        flatness = librosa.feature.spectral_flatness(y=y)[0]
        features['spectral_flatness_mean'] = float(np.mean(flatness))
        features['spectral_flatness_std'] = float(np.std(flatness))
        
        # 9. Mel Spectrogram Statistics
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr)
        features['mel_spec_mean'] = float(np.mean(mel_spec))
        features['mel_spec_std'] = float(np.std(mel_spec))
        
        return features
        
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        raise

def detect_ai_voice(features: dict, language: str) -> tuple[str, float]:
    """
    Detect if voice is AI-generated based on extracted features.
    This uses heuristic analysis of voice characteristics.
    """
    
    # Scoring system for AI detection
    ai_score = 0.0
    total_checks = 0
    
    # 1. Spectral consistency check
    # AI voices often have very consistent spectral characteristics
    if features['spectral_centroid_std'] < 200:
        ai_score += 1
    total_checks += 1
    
    # 2. MFCC variance check
    # AI voices tend to have lower variance in MFCCs
    mfcc_std_avg = np.mean(features['mfcc_std'])
    if mfcc_std_avg < 15:
        ai_score += 1
    total_checks += 1
    
    # 3. Zero crossing rate consistency
    # Human voices have more natural variation
    if features['zcr_std'] < 0.02:
        ai_score += 1
    total_checks += 1
    
    # 4. Pitch consistency check
    # AI voices often have unnaturally consistent pitch
    if features['pitch_std'] < 20 and features['pitch_mean'] > 0:
        ai_score += 1
    total_checks += 1
    
    # 5. Spectral flatness
    # AI voices tend to have different spectral flatness patterns
    if features['spectral_flatness_mean'] > 0.3 or features['spectral_flatness_std'] < 0.05:
        ai_score += 0.5
    total_checks += 1
    
    # 6. RMS energy consistency
    # AI voices have very consistent energy levels
    if features['rms_std'] < 0.01:
        ai_score += 0.5
    total_checks += 1
    
    # 7. Spectral contrast patterns
    # AI voices show different spectral contrast
    if features['spectral_contrast_mean'] > 25:
        ai_score += 0.5
    total_checks += 1
    
    # 8. Mel spectrogram analysis
    # Check for unnatural uniformity
    if features['mel_spec_std'] < 5:
        ai_score += 0.5
    total_checks += 1
    
    # 9. Pitch range check
    # AI voices often have limited pitch range
    if features['pitch_range'] < 50 and features['pitch_mean'] > 0:
        ai_score += 0.5
    total_checks += 1
    
    # Calculate final confidence
    raw_confidence = ai_score / total_checks
    
    # Adjust confidence based on language-specific patterns
    language_adjustments = {
        'tamil': 0.95,
        'english': 1.0,
        'hindi': 0.98,
        'malayalam': 0.96,
        'telugu': 0.97
    }
    
    adjusted_confidence = raw_confidence * language_adjustments.get(language, 1.0)
    
    # Threshold for classification
    threshold = 0.5
    
    if adjusted_confidence >= threshold:
        result = "AI_GENERATED"
        confidence = min(adjusted_confidence, 1.0)
    else:
        result = "HUMAN"
        confidence = min(1.0 - adjusted_confidence, 1.0)
    
    # Ensure confidence is in valid range
    confidence = max(0.0, min(1.0, confidence))
    
    return result, round(confidence, 4)

@app.post("/api/v1/detect", response_model=DetectionResponse)
async def detect_voice_base64(
    request: AudioRequestBase64,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Detect whether a voice sample is AI-generated or human (Base64 input).
    
    - **audio_base64**: Base64-encoded MP3 audio file
    - **language**: One of: tamil, english, hindi, malayalam, telugu
    - **X-API-Key**: Valid API key in header
    """
    
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Decode base64 audio
        audio_data = base64.b64decode(request.audio_base64)
        
        # Extract features
        logger.info(f"Processing base64 audio for language: {request.language}")
        features = extract_audio_features(audio_data)
        
        # Detect AI voice
        result, confidence = detect_ai_voice(features, request.language)
        
        # Prepare response
        response = DetectionResponse(
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
        
        logger.info(f"Detection result: {result} with confidence {confidence}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.post("/api/v1/detect-url", response_model=DetectionResponse)
async def detect_voice_url(
    request: AudioRequestURL,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Detect whether a voice sample is AI-generated or human (URL input).
    
    - **audio_url**: URL to MP3 audio file
    - **language**: One of: tamil, english, hindi, malayalam, telugu
    - **Authorization** or **X-API-Key**: Valid API key in header
    """
    
    # Accept API key from either Authorization or X-API-Key header
    api_key = x_api_key or authorization
    
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required in Authorization or X-API-Key header")
    
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Download audio from URL
        audio_data = download_audio_from_url(str(request.audio_url))
        
        # Extract features
        logger.info(f"Processing URL audio for language: {request.language}")
        features = extract_audio_features(audio_data)
        
        # Detect AI voice
        result, confidence = detect_ai_voice(features, request.language)
        
        # Prepare response
        response = DetectionResponse(
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
        
        logger.info(f"Detection result: {result} with confidence {confidence}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }

@app.get("/api/v1/info")
async def api_info():
    """Get API information"""
    return {
        "name": "AI Voice Detection API",
        "version": "1.0.0",
        "supported_languages": ["tamil", "english", "hindi", "malayalam", "telugu"],
        "endpoints": [
            "/api/v1/detect",
            "/api/v1/detect-url",
            "/api/v1/health",
            "/api/v1/info"
        ],
        "input_formats": [
            "base64 (via /detect endpoint)",
            "url (via /detect-url endpoint)"
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
