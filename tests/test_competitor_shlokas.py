import sys
import os
import re
from pathlib import Path

# Add backend to path
# Assuming script is in tests/ and backend is in backend/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, backend_path)

from core.chanda import Chanda
from config import settings

def parse_shlokas(file_path):
    """Extracts Sanskrit shlokas from the text file using Devanagari detection."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    shloka_blocks = []
    current_block = []
    
    # Devanagari unicode range
    devanagari_pattern = re.compile(r'[\u0900-\u097F]')

    for line in lines:
        line = line.strip()
        if not line:
            if current_block:
                shloka_blocks.append('\n'.join(current_block))
                current_block = []
            continue
            
        # Check if line contains Devanagari
        if devanagari_pattern.search(line):
            # Exclude lines that look like headers even if they have Devanagari (unlikely but possible)
            # But mostly headers are English in this file.
            current_block.append(line)
        else:
            # English text or other
            if current_block:
                shloka_blocks.append('\n'.join(current_block))
                current_block = []
    
    if current_block:
        shloka_blocks.append('\n'.join(current_block))
            
    return shloka_blocks

def test_competitor_dataset():
    """Runs the competitor's dataset through our engine."""
    # Calculate absolute path to competitor file
    # Script is in tests/, so we go up one level to root, then into repos/ShlokaYug
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    competitor_file = os.path.join(project_root, 'repos', 'ShlokaYug', 'shlokas.txt')
    
    if not os.path.exists(competitor_file):
        print(f"Competitor file not found at {competitor_file}")
        # Try alternative path if running from different context
        competitor_file = os.path.join(project_root, '..', 'repos', 'ShlokaYug', 'shlokas.txt')
        if not os.path.exists(competitor_file):
             print(f"Competitor file also not found at {competitor_file}")
             return

    print(f"Loading shlokas from {competitor_file}...")
    shlokas = parse_shlokas(competitor_file)
    print(f"Found {len(shlokas)} shlokas to test.")

    # Initialize Chanda engine
    chanda = Chanda(data_path=str(settings.DATA_DIR))
    
    results = []
    
    print("\n" + "="*60)
    print("RUNNING IDENTIFICATION ON COMPETITOR DATASET")
    print("="*60)

    for i, shloka in enumerate(shlokas, 1):
        print(f"\nTest Case #{i}:")
        print(f"Input:\n{shloka}")
        
        # Use identify_from_text with verse=True for holistic analysis
        result = chanda.identify_from_text(shloka, verse=True)
        
        identified = False
        primary_meter = "Unknown"
        
        # Check verse results
        if result and 'result' in result and 'verse' in result['result']:
            verse_results = result['result']['verse']
            if verse_results:
                # Check the first verse result
                vr = verse_results[0]
                if vr.get('chanda'):
                    # vr['chanda'] is a tuple: (['MeterName'], score)
                    meters, score = vr['chanda']
                    if meters:
                        primary_meter = meters[0]
                        identified = True
                        print(f"  -> Verse Identification: {primary_meter} (Score: {score})")
        
        # Also print line-level details if verse failed or for detail
        if not identified:
            print("  -> Verse identification failed. Checking lines...")
            if result and 'result' in result and 'line' in result['result']:
                for line_res in result['result']['line']:
                    line_text = line_res['line'].strip()
                    if not line_text: continue
                    
                    res = line_res['result']
                    meter = res.get('display_chanda_primary', 'Unknown')
                    if res.get('found'):
                        print(f"    -> Line: {line_text[:20]}... | Meter: {meter}")
                        # If any line is identified, count as partial success? 
                        # But we want verse identification.
        
        status = "✅ IDENTIFIED" if identified else "❌ FAILED"
        print(f"Result: {status}")
        results.append(identified)

    success_rate = (sum(results) / len(results)) * 100
    print("\n" + "="*60)
    print(f"FINAL REPORT: {sum(results)}/{len(results)} identified ({success_rate:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    test_competitor_dataset()
