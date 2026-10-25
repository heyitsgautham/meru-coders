#!/bin/bash
# Sanskrit TTS Installation Script
# Run with: bash install_tts.sh

set -e  # Exit on error

echo "====================================================================="
echo "Sanskrit TTS Installation Script"
echo "====================================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install basic dependencies
echo "Installing basic dependencies..."
pip install requests numpy soundfile --quiet
echo "✓ Basic dependencies installed"
echo ""

# Install PyTorch
echo "Installing PyTorch..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  Detected macOS - installing PyTorch for Mac..."
    pip install torch torchvision torchaudio --quiet
else
    echo "  Detected Linux/Windows - installing PyTorch with CUDA support..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --quiet
fi
echo "✓ PyTorch installed"
echo ""

# Install transformers and accelerate
echo "Installing transformers and accelerate..."
pip install transformers accelerate --quiet
echo "✓ Transformers installed"
echo ""

# Install parler-tts
echo "Installing parler-tts library..."
echo "  (This may take a few minutes...)"
pip install git+https://github.com/huggingface/parler-tts.git --quiet
echo "✓ Parler-TTS installed"
echo ""

# Optional: Install spectrogram dependencies
read -p "Install spectrogram generation support? (librosa, matplotlib) [y/N]: " install_spectrogram
if [[ $install_spectrogram =~ ^[Yy]$ ]]; then
    echo "Installing spectrogram dependencies..."
    pip install librosa matplotlib --quiet
    echo "✓ Spectrogram support installed"
    echo ""
fi

echo "====================================================================="
echo "Installation Complete!"
echo "====================================================================="
echo ""
echo "Next steps:"
echo "1. Test the installation:"
echo "   python sanskrit_tts.py \"ॐ नमः शिवाय\""
echo ""
echo "2. Generate with spectrogram:"
echo "   python sanskrit_tts.py \"ॐ नमः शिवाय\" --spectrogram"
echo ""
echo "3. Process multiple verses:"
echo "   python sanskrit_tts.py --file verses.txt"
echo ""
echo "Note: First run will download ~900MB model (one-time only)"
echo "====================================================================="
