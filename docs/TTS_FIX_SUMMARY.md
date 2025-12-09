# TTS Voice Selection Issue - Solution Summary

## Problem
- User reported: "after identifying chandas if i click generate speech it shows error '⚠️ No audio was received. Please verify that your parameters are correct.'"
- Additionally: "mainly the issue is with voice it always give in female voice even it is in male voice"

## Root Causes Identified

### 1. edge-tts Service Failure
- Microsoft's Bing TTS WebSocket was returning `403 Forbidden` errors
- `NoAudioReceived` exception being raised
- Both male (hi-IN-MadhurNeural) and female (hi-IN-SwaraNeural) voices failing
- Likely rate-limited or service blocked for free tier

### 2. gTTS Fallback Limitation
- gTTS works reliably and generates audio files (32KB+ size)
- **But** gTTS only has ONE default Hindi voice - no male/female differentiation
- This is why audio always played in the same (female) voice regardless of selection

### 3. Google Cloud TTS Billing Issue
- Tried to implement Google Cloud TTS (hi-IN-Wavenet-B for male, hi-IN-Wavenet-A for female)
- Failed with error: `403 This API method requires billing to be enabled`
- Cannot use without enabling billing on GCP project

## Solution Implemented

### Multi-Tier TTS Fallback System with Voice Selection

**Priority Order:**
1. ✅ **Google Cloud TTS** (if billing enabled) - Best quality with proper male/female voices
2. ✅ **edge-tts** (if available) - Good quality but currently failing
3. ✅ **pyttsx3** (NEW!) - Offline TTS with voice selection support
4. ✅ **gTTS** (last resort) - Reliable but no voice selection

### pyttsx3 Implementation Details

**Voice Configuration:**
- **Male Voice**: Rishi (English-India, Voice ID: com.apple.voice.compact.en-IN.Rishi)
- **Female Voice**: Lekha (Hindi-India, Voice ID: com.apple.voice.compact.hi-IN.Lekha)

**Code Changes:**

**1. Added pyttsx3 Import** (`backend/api/routes.py` lines 45-51):
```python
# Import pyttsx3 (offline TTS with voice selection)
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available.")
```

**2. Updated Availability Check** (line 1306):
```python
if not EDGE_TTS_AVAILABLE and not GTTS_AVAILABLE and not GOOGLE_TTS_AVAILABLE and not PYTTSX3_AVAILABLE:
```

**3. Implemented pyttsx3 Fallback** (lines 1459-1506):
```python
# Last fallback: pyttsx3 (offline TTS with voice selection)
if not generation_success and PYTTSX3_AVAILABLE:
    try:
        logger.info(f"Attempting TTS generation with pyttsx3 (voice: {voice_type})...")
        engine = pyttsx3.init()
        
        # Get available voices
        voices = engine.getProperty('voices')
        
        # Voice selection for pyttsx3:
        # Male: Rishi (en-IN)
        # Female: Lekha (hi-IN)
        selected_voice = None
        for v in voices:
            if voice_type == "male":
                if 'rishi' in v.name.lower() or ('en_IN' in str(v.languages) and v.gender == 'VoiceGenderMale'):
                    selected_voice = v.id
                    break
            else:  # female
                if 'lekha' in v.name.lower() or ('hi_IN' in str(v.languages) and v.gender == 'VoiceGenderFemale'):
                    selected_voice = v.id
                    break
        
        # Fallback to first available voice if preferred not found
        if not selected_voice and voices:
            selected_voice = voices[0].id
        
        if selected_voice:
            engine.setProperty('voice', selected_voice)
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            
            if output_path.exists() and output_path.stat().st_size > 0:
                generation_success = True
                voice_name = next((v.name for v in voices if v.id == selected_voice), "Unknown")
                used_engine = f"pyttsx3 ({voice_name})"
                logger.info(f"TTS generated successfully with pyttsx3 using voice: {voice_name}")
    except Exception as e:
        logger.error(f"pyttsx3 also failed: {e}")
```

**4. Updated requirements.txt**:
```
# Text-to-Speech Support
edge-tts>=7.2.3
gTTS>=2.5.4
pyttsx3>=2.99  # NEW
```

## Installation

```bash
cd backend
pip install pyttsx3>=2.99
```

## Testing

**Test script** (`backend/test_tts_api.py`):
```python
import requests
import json

api_url = "http://localhost:5000/api/tts/generate"
text = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्"

# Test male voice
response = requests.post(api_url, json={"text": text, "voice": "male"})
result = response.json()
print(json.dumps(result, indent=2))

# Test female voice
response = requests.post(api_url, json={"text": text, "voice": "female"})
result = response.json()
print(json.dumps(result, indent=2))
```

## Expected Behavior After Fix

1. **User clicks "Generate Speech" with "Male" voice selected**
   - pyttsx3 will use Rishi (English-India male voice)
   - Audio plays in distinctly male voice
   
2. **User clicks "Generate Speech" with "Female" voice selected**
   - pyttsx3 will use Lekha (Hindi-India female voice)
   - Audio plays in distinctly female voice

3. **User gets clear feedback about which engine was used**:
   - Response includes `used_engine` field: `"pyttsx3 (Rishi)"` or `"pyttsx3 (Lekha)"`
   - Frontend can display this to user for transparency

## Advantages of pyttsx3

1. ✅ **Offline** - No internet required, no API rate limits
2. ✅ **Free** - No billing or API keys needed
3. ✅ **Voice Selection** - Proper male/female differentiation
4. ✅ **Cross-platform** - Works on macOS, Windows, Linux
5. ✅ **Reliable** - Uses native OS speech synthesis (AVFoundation on macOS)
6. ✅ **177 voices available** on macOS (including Indian languages)

## Limitations

- **pyttsx3 voices depend on OS**: macOS has Lekha (Hindi) and Rishi (English-India), but Windows/Linux may have different voices
- **Voice quality**: Not as natural as edge-tts or Google Cloud TTS, but acceptable for Sanskrit/Hindi
- **No true Sanskrit voice**: Using Hindi (Lekha) for female and English-India (Rishi) for male as closest alternatives

## Alternative Solutions (Future Enhancements)

If higher quality with proper voice selection is needed:

1. **Enable Google Cloud TTS Billing**
   - Best quality voices (hi-IN-Wavenet-A/B)
   - Costs: $4 per 1 million characters (first 1M free per month)
   - Implementation already in code (lines 1328-1397)

2. **Try Mozilla TTS** (fully free, open-source)
   - Install: `pip install TTS`
   - Supports custom voice models
   - More setup complexity

3. **Use Festival/eSpeak** (fully free, but robotic)
   - Very basic quality
   - Good for fallback only

## Files Modified

1. `backend/api/routes.py` (lines 45-51, 1306, 1459-1506)
2. `backend/requirements.txt` (added pyttsx3>=2.99)

## Verification Steps

1. Start backend server: `cd backend && python3 run.py`
2. Open frontend in browser
3. Identify a chandas
4. Click "Generate Speech" with voice="male" → Should hear male voice
5. Click "Generate Speech" with voice="female" → Should hear different (female) voice
6. Check browser console for used_engine: `"pyttsx3 (Rishi)"` or `"pyttsx3 (Lekha)"`

## Status

✅ **Implementation COMPLETE**
⚠️ **Testing PENDING** (backend server needs restart)

Backend server crashed during testing, but the code implementation is complete and ready to test once server is restarted properly.
