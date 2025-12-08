#!/usr/bin/env python3
"""
Extract all verses from Bhagavad Gita JSON files and save to CSV.
This script reads all 18 chapters and extracts just the verse text.
"""

import json
import csv
import os
from pathlib import Path

def extract_verse_text(text):
    """
    Extract the actual verse from the text field.
    The text field contains speaker info, verse, and reference numbers.
    We want to extract just the Sanskrit verse lines.
    """
    # Remove reference pattern like ।।12.1।। at the end
    import re
    text = re.sub(r'।।\d+\.\d+।।', '', text)
    
    # Split by newlines or the speaker pattern
    lines = text.strip().split('\n')
    verse_lines = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
        # Skip speaker info (contains "उवाच")
        if 'उवाच' in line:
            continue
        # Add the verse line
        verse_lines.append(line)
    
    result = '\n'.join(verse_lines)
    
    # Handle cases where there are no newlines - split by उवाच pattern
    if 'उवाच' in result:
        # Split at उवाच and take the part after it
        parts = result.split('उवाच')
        if len(parts) > 1:
            result = parts[1].strip()
    
    return result.strip()

def main():
    # Path to the Bhagavad Gita chapters
    base_path = Path("/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/repos/DharmicData/SrimadBhagvadGita")
    
    # Output CSV file
    output_file = Path("/Users/gauthamkrishna/Projects/chanda/repos/meru-coders/backend/data/bhagavad_gita_verses.csv")
    
    all_verses = []
    
    # Process all 18 chapters
    for chapter_num in range(1, 19):
        json_file = base_path / f"bhagavad_gita_chapter_{chapter_num}.json"
        
        if not json_file.exists():
            print(f"Warning: {json_file} not found, skipping...")
            continue
        
        print(f"Processing Chapter {chapter_num}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract verses from the chapter
        for verse_data in data.get('BhagavadGitaChapter', []):
            text = verse_data.get('text', '')
            verse_text = extract_verse_text(text)
            
            if verse_text:
                all_verses.append({
                    'chapter': verse_data.get('chapter'),
                    'verse': verse_data.get('verse'),
                    'verse_text': verse_text
                })
    
    # Write to CSV
    print(f"\nWriting {len(all_verses)} verses to CSV...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['verse_text'])
        writer.writeheader()
        
        for verse in all_verses:
            writer.writerow({'verse_text': verse['verse_text']})
    
    print(f"\n✅ Successfully extracted {len(all_verses)} verses!")
    print(f"📄 Output file: {output_file}")
    print(f"\nBreakdown by chapter:")
    
    # Show breakdown by chapter
    chapter_counts = {}
    for verse in all_verses:
        ch = verse['chapter']
        chapter_counts[ch] = chapter_counts.get(ch, 0) + 1
    
    for ch in sorted(chapter_counts.keys()):
        print(f"  Chapter {ch:2d}: {chapter_counts[ch]:3d} verses")
    
    return len(all_verses)

if __name__ == '__main__':
    total = main()
    print(f"\n📊 Total verses in Bhagavad Gita: {total}")
