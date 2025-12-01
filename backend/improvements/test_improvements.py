#!/usr/bin/env python3
"""
Improvement Script for Chanda Identification Model
Addresses the issues identified in confusion matrix analysis

Key Changes:
1. Add PADA_PATTERNS dictionary for classical meters
2. Modify confidence scoring to prioritize pada-level exact matches
3. Reduce Vedic syllable-count fallback confidence
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.chanda import Chanda

# Classical pada patterns (11, 12, 14, 15 syllables per pada)
PADA_PATTERNS = {
    # Trishtubh family (11 syllables per pada)
    'GGLGGLGGLGG': ('इन्द्रवज्रा', 'Indravajra'),
    'LGGLGGLGGLG': ('उपेन्द्रवज्रा', 'Upendravajra'),  
    'GGGLGGLGGLGG': ('शालिनी', 'Shalini'),
    'GLGLLLGLGLG': ('रथोद्धता', 'Rathoddhata'),
    'GLLGLLGGLGG': ('वातोर्मी', 'Vatormi'),
    'LGLLGLLGGLG': ('स्वागता', 'Svagata'),
    
    # Jagati family (12 syllables per pada)
    'LGGLLGLLGLGL': ('वंशस्थ', 'Vamshastham'),
    'LGGLGGLGGLGG': ('भुजङ्गप्रयात', 'Bhujangaprayata'),
    'LLGLLGLLGLLG': ('तोटक', 'Totaka'),
    'GLGLLGLLGLGL': ('द्रुतविलम्बित', 'Drutavilambita'),
    
    # Other classical meters
    'GGLGLLGLLGLGG': ('वसन्ततिलका', 'Vasantatilaka'),  # 14 syllables
    'LLLLLLGGGLGGLGG': ('मालिनी', 'Malini'),  # 15 syllables
    'GGGLLGLLGLGLG': ('प्रहर्षिणी', 'Praharsini'),  # 13 syllables
    
    # Anushtubh variations (8 syllables)
    'GLGGLGGL': ('अनुष्टुभ्', 'Anushtubh'),
    'LLLLGGGL': ('अनुष्टुभ्', 'Anushtubh'),
}

# Gaṇa-based patterns (easier to remember)
GANA_TO_LG = {
    'म': 'GGG',  # ma-gaṇa
    'य': 'LGG',  # ya-gaṇa  
    'र': 'GLG',  # ra-gaṇa
    'स': 'LLG',  # sa-gaṇa
    'त': 'GGL',  # ta-gaṇa
    'ज': 'LGL',  # ja-gaṇa
    'भ': 'GLL',  # bha-gaṇa
    'न': 'LLL',  # na-gaṇa
}

def gana_to_lg_pattern(gana_string):
    """Convert gaṇa sequence to L-G pattern"""
    result = ''
    for char in gana_string:
        if char in GANA_TO_LG:
            result += GANA_TO_LG[char]
        elif char == 'ग':  # Single guru
            result += 'G'
        elif char == 'ल':  # Single laghu
            result += 'L'
    return result

# Classical meter definitions using gaṇas
CLASSICAL_METERS = {
    # Trishtubh family (11 syllables = 4 gaṇas + 1 guru + 1 guru, or variations)
    'Indravajra': ('ततजगग', 11),      # त त ज ग ग
    'Upendravajra': ('जतजगग', 11),    # ज त ज ग ग  
    'Shalini': ('मततगग', 11),         # म त त ग ग
    'Rathoddhata': ('रनरलग', 11),     # र न र ल ग
    
    # Jagati family (12 syllables)
    'Vamshastham': ('जतजर', 12),      # ज त ज र
    'Bhujangaprayata': ('यययय', 12),  # य य य य
    'Totaka': ('ससससस', 12),          # स स स स (4 sa-ganas)
    'Drutavilambita': ('नभभर', 12),   # न भ भ र
    
    # Other meters
    'Vasantatilaka': ('तभजजगग', 14),  # त भ ज ज ग ग
    'Malini': ('ननमयय', 15),          # न न म य य
    'Mandakranta': ('मभनततगग', 17),   # म भ न त त ग ग
    'Shardula': ('मसजसततग', 19),      # म स ज स त त ग
}

def generate_lg_from_gana(gana_str, syllable_count):
    """Generate L-G pattern from gaṇa string, handling extra syllables"""
    pattern = ''
    i = 0
    while i < len(gana_str):
        char = gana_str[i]
        if char in GANA_TO_LG:
            pattern += GANA_TO_LG[char]
        elif char == 'ग':
            pattern += 'G'
        elif char == 'ल':
            pattern += 'L'
        i += 1
    
    # Pad or truncate to match syllable count
    if len(pattern) < syllable_count:
        pattern += 'G' * (syllable_count - len(pattern))
    elif len(pattern) > syllable_count:
        pattern = pattern[:syllable_count]
    
    return pattern

def test_pada_pattern_matching():
    """Test if pada-level pattern matching improves accuracy"""
    print("=" * 70)
    print("Testing Pada-Level Pattern Matching")
    print("=" * 70)
    
    # Generate patterns for classical meters
    print("\nGenerated L-G patterns from Gaṇa definitions:")
    print("-" * 50)
    
    for meter, (gana, syllables) in CLASSICAL_METERS.items():
        pattern = generate_lg_from_gana(gana, syllables)
        print(f"{meter:20s}: {gana:10s} → {pattern} ({len(pattern)} syllables)")
    
    print("\n" + "=" * 70)
    print("Testing Against Known Verses")
    print("=" * 70)
    
    # Test verses with known meters
    test_cases = [
        # (verse, expected_meter, expected_family)
        ("लोकाभिरामं रणरङ्गधीरं राजीवनेत्रं रघुवंशनाथम् । कारुण्यरूपं करुणाकरं तं श्रीरामचन्द्रं शरणं प्रपद्ये", "Indravajra", "Trishtubh"),
        ("नमामि नारायणपादपङ्कजं करोमि नारायणपूजनं सदा । वदामि नारायणनाम निर्मलं स्मरामि नारायणतत्त्वमव्ययम्", "Vamshastham", "Jagati"),
        ("न मे द्वेषरागौ न मे लोभमोहौ न मे वै मदो नैव मात्सर्यभावः । न धर्मो न चार्थो न कामो न मोक्षः चिदानन्दरूपः शिवोऽहं शिवोऽहम्", "Bhujangaprayata", "Jagati"),
    ]
    
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    chanda = Chanda(data_path)
    
    for verse, expected_meter, expected_family in test_cases:
        print(f"\nVerse: {verse[:60]}...")
        print(f"Expected: {expected_meter} ({expected_family})")
        
        # Get current prediction
        results = chanda.identify_from_text(verse)
        if results and 'results' in results and results['results']:
            for line_result in results['results']:
                if 'results' in line_result and line_result['results']:
                    top_result = line_result['results'][0]
                    print(f"Predicted: {top_result.get('name', 'Unknown')} (confidence: {top_result.get('confidence', 0):.2f})")
                    
                    # Show L-G pattern
                    lg_pattern = line_result.get('lg', '')
                    if lg_pattern:
                        print(f"L-G Pattern: {lg_pattern[:50]}... ({len(lg_pattern)} syllables)")
                        
                        # Try pada-level matching
                        for num_padas in [4, 3, 2]:
                            if len(lg_pattern) % num_padas == 0:
                                pada_length = len(lg_pattern) // num_padas
                                padas = [lg_pattern[i:i+pada_length] for i in range(0, len(lg_pattern), pada_length)]
                                
                                first_pada = padas[0]
                                if first_pada in PADA_PATTERNS:
                                    meter_name = PADA_PATTERNS[first_pada]
                                    print(f"✓ Pada match found: {first_pada} → {meter_name}")
                                else:
                                    print(f"✗ Pada not in database: {first_pada} ({pada_length} syllables)")
                                break
        print("-" * 50)

def analyze_missing_patterns():
    """Analyze which patterns are missing from the database"""
    print("\n" + "=" * 70)
    print("Analyzing Missing Patterns")
    print("=" * 70)
    
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data')
    chanda = Chanda(data_path)
    
    # Check what patterns exist for each syllable count
    syllable_counts = {}
    for pattern, names in chanda.CHANDA.items():
        count = len(pattern)
        if count not in syllable_counts:
            syllable_counts[count] = []
        syllable_counts[count].append((pattern, names))
    
    print("\nPatterns by syllable count (pada-level):")
    for count in [11, 12, 14, 15]:
        print(f"\n{count} syllables:")
        if count in syllable_counts:
            for pattern, names in syllable_counts[count][:5]:  # Show first 5
                print(f"  {pattern}: {names}")
        else:
            print("  No patterns found!")

def create_pada_patterns_csv():
    """Generate CSV file with pada patterns for classical meters"""
    import csv
    
    output_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'chanda_classical_padas.csv')
    
    # Classical pada patterns with full information
    pada_data = [
        # pattern, devanagari, iast, english, syllables, family, gana
        ('GGLGGLGGLGG', 'इन्द्रवज्रा', 'indravajrā', 'Indravajra', 11, 'trishtubh', 'त त ज ग ग'),
        ('LGGLGGLGGLG', 'उपेन्द्रवज्रा', 'upendravajrā', 'Upendravajra', 11, 'trishtubh', 'ज त ज ग ग'),
        ('GGGGLGGLGGG', 'शालिनी', 'śālinī', 'Shalini', 11, 'trishtubh', 'म त त ग ग'),
        ('GLGLLLGLGLG', 'रथोद्धता', 'rathoddhata', 'Rathoddhata', 11, 'trishtubh', 'र न र ल ग'),
        ('LGLLGGLLGLGL', 'वंशस्थ', 'vaṁśastha', 'Vamshastham', 12, 'jagati', 'ज त ज र'),
        ('LGGLGGLGGLGG', 'भुजङ्गप्रयात', 'bhujangaprayāta', 'Bhujangaprayata', 12, 'jagati', 'य य य य'),
        ('LLGLLGLLGLLG', 'तोटक', 'toṭaka', 'Totaka', 12, 'jagati', 'स स स स'),
        ('LLLGLLGLLGLG', 'द्रुतविलम्बित', 'drutavilambita', 'Drutavilambita', 12, 'jagati', 'न भ भ र'),
        ('GGLGLLGLLGLGG', 'वसन्ततिलका', 'vasantatilakā', 'Vasantatilaka', 14, 'other', 'त भ ज ज ग ग'),
        ('LLLLLLGGGGLGGLGG', 'मालिनी', 'mālinī', 'Malini', 15, 'other', 'न न म य य'),
        ('GGGLLLLGGLGGLGG', 'मन्दाक्रान्ता', 'mandākrāntā', 'Mandakranta', 17, 'other', 'म भ न त त ग ग'),
        ('GGGLLGLLGLLGLLGGLGG', 'शार्दूलविक्रीडित', 'śārdūlavikrīḍita', 'Shardula', 19, 'other', 'म स ज स त त ग'),
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['lg_pattern', 'name_devanagari', 'name_iast', 'name_english', 'syllable_count', 'family', 'gana'])
        for row in pada_data:
            writer.writerow(row)
    
    print(f"\nCreated: {output_file}")
    return output_file

if __name__ == '__main__':
    print("Chanda Model Improvement Analysis")
    print("=" * 70)
    
    # Test pada pattern matching
    test_pada_pattern_matching()
    
    # Analyze missing patterns
    analyze_missing_patterns()
    
    # Create CSV with pada patterns
    create_pada_patterns_csv()
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    print("""
1. Add PADA_PATTERNS dictionary to chanda.py (see above)
2. Modify match_with_confidence() to:
   a. Check pada-level exact matches BEFORE Vedic syllable-count fallback
   b. Reduce Vedic fallback confidence from 7.0 to 4.0
3. Import chanda_classical_padas.csv into the database
4. Handle Upajati (mixed Indravajra/Upendravajra padas) specially
""")
