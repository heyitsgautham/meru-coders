"""
Sanskrit Text-to-Speech Module
Uses rverma0631/Sanskrit_TTS model from Hugging Face

This module provides both API-based and local inference options for
converting Sanskrit text (Devanagari) to speech audio files.
"""

import os
import requests
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Literal

# Optional imports for local inference and spectrogram generation
try:
    import torch
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    import librosa
    import librosa.display
    import matplotlib.pyplot as plt
    SPECTROGRAM_AVAILABLE = True
except ImportError:
    SPECTROGRAM_AVAILABLE = False


class SanskritTTS:
    """Sanskrit Text-to-Speech converter using Hugging Face model."""
    
    MODEL_ID = "ai4bharat/indic-parler-tts"
    HF_API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
    DEFAULT_SPEAKER = "Aryan"  # Recommended Sanskrit speaker
    DEFAULT_DESCRIPTION = (
        "Aryan speaks in a clear, steady voice with excellent pronunciation. "
        "The recording is of very high quality with no background noise."
    )
    
    def __init__(
        self,
        hf_token: Optional[str] = None,
        output_dir: str = "./outputs",
        mode: Literal["api", "local", "auto"] = "auto",
        speaker: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize Sanskrit TTS.
        
        Args:
            hf_token: Hugging Face API token (required for API mode)
            output_dir: Directory to save output files
            mode: "api" (HF Inference API), "local" (load model locally), 
                  or "auto" (choose based on availability)
            speaker: Speaker name (default: "Aryan" for Sanskrit)
            description: Voice description (auto-generated if None)
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.speaker = speaker or self.DEFAULT_SPEAKER
        self.description = description or self.DEFAULT_DESCRIPTION
        
        # Determine mode
        if mode == "auto":
            # Note: API mode may not be available for this model
            if TRANSFORMERS_AVAILABLE:
                self.mode = "local"
                print("ℹ️  Auto mode: Using local inference (API not available for this model)")
            else:
                raise ValueError(
                    "Auto mode requires local inference for this model. "
                    "Please install dependencies with: pip install -r requirements_tts.txt"
                )
        else:
            self.mode = mode
            
        # Validate mode requirements
        if self.mode == "api":
            if not self.hf_token:
                raise ValueError("API mode requires HF_TOKEN")
            print("⚠️  Warning: API mode may not be available for ai4bharat/indic-parler-tts")
            print("   The model may not support Inference API. Consider using local mode instead.")
            print("   Use: --mode local")
        if self.mode == "local" and not TRANSFORMERS_AVAILABLE:
            raise ValueError(
                "Local mode requires parler-tts and dependencies. "
                "Install with: pip install -r requirements_tts.txt"
            )
        
        # Initialize local model if needed
        self.model = None
        self.tokenizer = None
        self.description_tokenizer = None
        if self.mode == "local":
            self._init_local_model()
    
    def _init_local_model(self):
        """Initialize local TTS model."""
        try:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            print(f"Loading {self.MODEL_ID} on {device}...")
            
            self.model = ParlerTTSForConditionalGeneration.from_pretrained(
                self.MODEL_ID
            ).to(device)
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
            self.description_tokenizer = AutoTokenizer.from_pretrained(
                self.model.config.text_encoder._name_or_path
            )
            
            print(f"✓ Loaded {self.MODEL_ID} locally on {device}")
        except Exception as e:
            raise RuntimeError(f"Failed to load local model: {e}")
    
    def synthesize_api(
        self, 
        text: str, 
        description: Optional[str] = None,
        wait_for_model: bool = True
    ) -> bytes:
        """
        Synthesize speech using Hugging Face Inference API.
        
        Args:
            text: Sanskrit text (Devanagari script recommended)
            description: Voice description (uses default if None)
            wait_for_model: Wait if model is loading (cold start)
            
        Returns:
            Audio data as bytes (WAV format)
        """
        if not self.hf_token:
            raise ValueError("HF_TOKEN required for API mode")
        
        desc = description or self.description
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": {"text": text, "description": desc},
            "options": {"wait_for_model": wait_for_model}
        }
        
        try:
            response = requests.post(
                self.HF_API_URL,
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            response.raise_for_status()
            
            # Check if response is audio bytes or JSON error
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                error_data = response.json()
                raise RuntimeError(f"API error: {error_data}")
            
            return response.content
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API request failed: {e}")
    
    def synthesize_local(
        self,
        text: str,
        description: Optional[str] = None
    ) -> tuple[np.ndarray, int]:
        """
        Synthesize speech using local model.
        
        Args:
            text: Sanskrit text (Devanagari script recommended)
            description: Voice description (uses default if None)
            
        Returns:
            Tuple of (audio_array, sample_rate)
        """
        if not self.model:
            raise RuntimeError("Local model not initialized")
        
        try:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            desc = description or self.description
            
            # Tokenize inputs
            description_input_ids = self.description_tokenizer(
                desc, return_tensors="pt"
            ).to(device)
            
            prompt_input_ids = self.tokenizer(
                text, return_tensors="pt"
            ).to(device)
            
            # Generate audio
            generation = self.model.generate(
                input_ids=description_input_ids.input_ids,
                attention_mask=description_input_ids.attention_mask,
                prompt_input_ids=prompt_input_ids.input_ids,
                prompt_attention_mask=prompt_input_ids.attention_mask
            )
            
            audio_arr = generation.cpu().numpy().squeeze()
            sample_rate = self.model.config.sampling_rate
            
            return audio_arr, sample_rate
                
        except Exception as e:
            raise RuntimeError(f"Local synthesis failed: {e}")
    
    def synthesize(
        self,
        text: str,
        output_filename: Optional[str] = None,
        generate_spectrogram: bool = False
    ) -> Dict[str, Path]:
        """
        Synthesize speech and save to file.
        
        Args:
            text: Sanskrit text (Devanagari script recommended)
            output_filename: Base filename (without extension). 
                           If None, generates timestamped filename.
            generate_spectrogram: Also generate spectrogram image
            
        Returns:
            Dictionary with paths: {"audio": Path, "spectrogram": Path | None}
        """
        # Generate filename
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"sanskrit_tts_{timestamp}"
        
        audio_path = self.output_dir / f"{output_filename}.wav"
        
        # Synthesize based on mode
        if self.mode == "api":
            print(f"🎤 Synthesizing via API: {text[:50]}...")
            print(f"   Speaker: {self.speaker}")
            audio_bytes = self.synthesize_api(text, self.description)
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            print(f"✓ Saved audio to {audio_path}")
            
        else:  # local
            print(f"🎤 Synthesizing locally: {text[:50]}...")
            print(f"   Speaker: {self.speaker}")
            audio_array, sample_rate = self.synthesize_local(text, self.description)
            if not SOUNDFILE_AVAILABLE:
                raise RuntimeError("soundfile required for local synthesis. Install with: pip install soundfile")
            sf.write(audio_path, audio_array, sample_rate)
            print(f"✓ Saved audio to {audio_path}")
        
        result = {"audio": audio_path, "spectrogram": None}
        
        # Generate spectrogram if requested
        if generate_spectrogram:
            if not SPECTROGRAM_AVAILABLE:
                print("⚠ Spectrogram generation requires librosa and matplotlib")
                print("  Install with: pip install librosa matplotlib")
            else:
                spec_path = self.generate_spectrogram(
                    audio_path,
                    self.output_dir / f"{output_filename}_spectrogram.png"
                )
                result["spectrogram"] = spec_path
        
        return result
    
    def generate_spectrogram(
        self,
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        figsize: tuple = (10, 4),
        dpi: int = 200
    ) -> Path:
        """
        Generate spectrogram image from audio file.
        
        Args:
            audio_path: Path to audio file
            output_path: Path for output image. If None, uses audio_path with .png
            figsize: Figure size (width, height)
            dpi: Image resolution
            
        Returns:
            Path to generated spectrogram image
        """
        if not SPECTROGRAM_AVAILABLE:
            raise RuntimeError(
                "Spectrogram generation requires librosa and matplotlib. "
                "Install with: pip install librosa matplotlib"
            )
        
        audio_path = Path(audio_path)
        if output_path is None:
            output_path = audio_path.with_suffix(".png")
        else:
            output_path = Path(output_path)
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=None)
        
        # Compute spectrogram
        S = librosa.stft(y, n_fft=1024, hop_length=256)
        S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
        
        # Plot
        plt.figure(figsize=figsize)
        librosa.display.specshow(
            S_db,
            sr=sr,
            hop_length=256,
            x_axis='time',
            y_axis='hz',
            cmap='viridis'
        )
        plt.colorbar(format='%+2.0f dB')
        plt.title('Sanskrit TTS Spectrogram')
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Saved spectrogram to {output_path}")
        return output_path
    
    def batch_synthesize(
        self,
        texts: list[str],
        output_prefix: str = "batch",
        generate_spectrograms: bool = False
    ) -> list[Dict[str, Path]]:
        """
        Synthesize multiple texts in batch.
        
        Args:
            texts: List of Sanskrit texts
            output_prefix: Prefix for output filenames
            generate_spectrograms: Generate spectrograms for all
            
        Returns:
            List of result dictionaries
        """
        results = []
        for i, text in enumerate(texts, 1):
            print(f"\n[{i}/{len(texts)}] Processing: {text[:60]}...")
            try:
                result = self.synthesize(
                    text,
                    output_filename=f"{output_prefix}_{i:03d}",
                    generate_spectrogram=generate_spectrograms
                )
                results.append(result)
            except Exception as e:
                print(f"✗ Failed: {e}")
                results.append({"error": str(e)})
        
        return results


def main():
    """CLI interface for Sanskrit TTS."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Sanskrit Text-to-Speech using Hugging Face"
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Sanskrit text to synthesize (Devanagari)"
    )
    parser.add_argument(
        "-f", "--file",
        help="Text file with Sanskrit verses (one per line)"
    )
    parser.add_argument(
        "-o", "--output",
        default="./outputs",
        help="Output directory (default: ./outputs)"
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["api", "local", "auto"],
        default="auto",
        help="Inference mode (default: auto)"
    )
    parser.add_argument(
        "-s", "--spectrogram",
        action="store_true",
        help="Generate spectrogram images"
    )
    parser.add_argument(
        "--token",
        help="Hugging Face API token (or set HF_TOKEN env var)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.text and not args.file:
        parser.error("Either provide text or --file")
    
    # Initialize TTS
    try:
        tts = SanskritTTS(
            hf_token=args.token,
            output_dir=args.output,
            mode=args.mode
        )
        print(f"✓ Initialized Sanskrit TTS (mode: {tts.mode})")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return 1
    
    # Process input
    if args.text:
        # Single text
        result = tts.synthesize(args.text, generate_spectrogram=args.spectrogram)
        print(f"\n✓ Complete! Audio: {result['audio']}")
        if result['spectrogram']:
            print(f"  Spectrogram: {result['spectrogram']}")
    else:
        # Batch from file
        with open(args.file, 'r', encoding='utf-8') as f:
            texts = [line.strip() for line in f if line.strip()]
        
        print(f"\n📄 Processing {len(texts)} texts from {args.file}")
        results = tts.batch_synthesize(
            texts,
            output_prefix=Path(args.file).stem,
            generate_spectrograms=args.spectrogram
        )
        
        success = sum(1 for r in results if "error" not in r)
        print(f"\n✓ Complete! {success}/{len(texts)} successful")
    
    return 0


if __name__ == "__main__":
    exit(main())
