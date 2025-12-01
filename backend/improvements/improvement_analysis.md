# Model Improvement Analysis - Chandojñānam

## Executive Summary

**Current Accuracy**: 17.4% (Top-1) | 19.3% (Top-3) | 65.1% (Family-Level)

The model correctly identifies the **family** of meters (Trishtubh-family, Jagati-family) but fails to distinguish between **specific classical patterns** within each family.

---

## Root Cause Analysis

### Issue 1: Confidence Scoring Prioritizes Vedic Families Over Classical Patterns

**Problem**: The `match_with_confidence()` function assigns:
- Vedic syllable-count matching: **7.0 confidence**
- Pada-level sama matching: **8.0 confidence**
- Exact L-G pattern matching: **10.0 confidence** (but only checked first)

However, when the exact pattern doesn't exist in the database, the Vedic syllable-count result is returned, causing:
- Indravajra → Trishtubh (7 failures)
- Bhujangaprayata → Jagati (7 failures)
- Vasantatilaka → Ushnik (6 failures)

**Solution**: 
1. Add exact L-G patterns for all Trishtubh-family and Jagati-family meters
2. Lower Vedic syllable-count confidence to 4.0 (below fuzzy matching)
3. Prioritize database patterns over syllable-count guessing

### Issue 2: Missing Classical Meter Patterns

The database lacks specific patterns for many meters tested. Here are the patterns that need to be added:

#### Trishtubh Family (44 syllables = 4×11)

| Meter | Gaṇa Pattern | L-G Pattern |
|-------|--------------|-------------|
| **Indravajra** | त त ज ग ग | GGLGGLGGLGG × 4 |
| **Upendravajra** | ज त ज ग ग | LGGLGGLGGLGG × 4 |
| **Upajāti** | Mixed त/ज in first position | Various combinations |
| **Śālinī** | म त त ग ग | GGGLGGLGGLGG × 4 |
| **Rathoddhata** | र न र ल ग | GLGLLGLGLLLG × 4 |

#### Jagati Family (48 syllables = 4×12)

| Meter | Gaṇa Pattern | L-G Pattern |
|-------|--------------|-------------|
| **Vaṁśasthavila** | ज त ज र | LGGLLGLGGLGLG × 4 |
| **Bhujangaprayāta** | य य य य | LGGLGGLGGLGG × 4 |
| **Toṭaka** | स स स स | LLGLLGLLGLLG × 4 |

#### Other Meters

| Meter | Syllables | Gaṇa Pattern | L-G Pattern |
|-------|-----------|--------------|-------------|
| **Vasantatilaka** | 56 (4×14) | त भ ज ज ग ग | GGLGLLGLLGLGG × 4 |
| **Mālinī** | 60 (4×15) | न न म य य | LLLLLLGGGLGGLGG × 4 |
| **Praharṣiṇī** | 52 (4×13) | म न ज र ग | GGGLLGLLGLGLG × 4 |

### Issue 3: Database Has Patterns But Model Doesn't Match

Some meters like शालिनी (Shalini), वसन्ततिलका (Vasantatilaka) are in the database, but only match their lakṣaṇa (definition verse), not actual verses.

**Reason**: The stored pattern may be for the lakṣaṇa śloka, not the actual meter pattern.

---

## Recommended Code Changes

### 1. Add Classical Meter Patterns to Database

Add these to `chanda_sama.csv` (or create new file `chanda_classical.csv`):

```csv
lg_pattern,name_devanagari,name_iast,name_english,syllable_count,family
GGLGGLGGLGG,इन्द्रवज्रा,indravajrā,Indravajra,11,trishtubh
LGGLGGLGGLGG,उपेन्द्रवज्रा,upendravajrā,Upendravajra,11,trishtubh
GGGLGGLGGLGG,शालिनी,śālinī,Shalini,11,trishtubh
GLGLLGLGLLLG,रथोद्धता,rathoddhata,Rathoddhata,11,trishtubh
LGGLLGLGGLGLG,वंशस्थ,vaṁśastha,Vamshastham,12,jagati
LGGLGGLGGLGGL,भुजङ्गप्रयात,bhujangaprayāta,Bhujangaprayata,12,jagati
LLGLLGLLGLLG,तोटक,toṭaka,Totaka,12,jagati
GGLGLLGLLGLGG,वसन्ततिलका,vasantatilakā,Vasantatilaka,14,other
LLLLLLGGGLGGLGG,मालिनी,mālinī,Malini,15,other
```

### 2. Modify `match_with_confidence()` to Check Pada Patterns

```python
def match_with_confidence(self, lg_pattern, fuzzy=False, max_fuzzy=10):
    results = []
    syllable_count = len(lg_pattern)
    
    # Level 1: Exact match (highest confidence)
    if lg_pattern in self.CHANDA:
        for meter_name in self.CHANDA[lg_pattern]:
            results.append((meter_name, 10.0, 'exact'))
    
    # Level 2: Pada-level exact matching (NEW - check individual padas)
    for num_padas in [4, 3, 2]:
        padas = self.split_into_padas(lg_pattern, num_padas)
        if padas:
            # Check each pada against known pada patterns
            first_pada = padas[0]
            if first_pada in self.PADA_PATTERNS:  # NEW dictionary
                meter_name = self.PADA_PATTERNS[first_pada]
                all_sama = all(pada == first_pada for pada in padas)
                if all_sama:
                    results.append((meter_name, 9.5, 'pada_exact'))
                else:
                    # Check for Upajati-like meters (mixed padas)
                    results.append((meter_name, 8.5, 'pada_mixed'))
    
    # Level 3: Syllable count + fuzzy pada matching (REDUCED confidence)
    vedic_meter, vedic_info = self.identify_vedic_meter(syllable_count, lg_pattern)
    if vedic_meter:
        confidence = 4.0  # REDUCED from 7.0
        results.append(((vedic_meter, ''), confidence, 'vedic_syllable'))
    
    # ... rest of function
```

### 3. Add PADA_PATTERNS Dictionary

```python
PADA_PATTERNS = {
    # Trishtubh family (11 syllables per pada)
    'GGLGGLGGLGG': 'इन्द्रवज्रा',      # Indravajra
    'LGGLGGLGGLG': 'उपेन्द्रवज्रा',    # Upendravajra
    'GGGLGGLGGLG': 'शालिनी',          # Shalini
    'GLGLLGLGLLG': 'रथोद्धता',        # Rathoddhata
    
    # Jagati family (12 syllables per pada)
    'LGGLLGLGGLGL': 'वंशस्थ',         # Vamshastham
    'LGGLGGLGGLGG': 'भुजङ्गप्रयात',    # Bhujangaprayata
    'LLGLLGLLGLLG': 'तोटक',           # Totaka
    
    # Other meters
    'GGLGLLGLLGLGG': 'वसन्ततिलका',    # Vasantatilaka (14)
    'LLLLLLGGGLGGLGG': 'मालिनी',      # Malini (15)
}
```

---

## Implementation Priority

1. **HIGH**: Add pada-level pattern matching with `PADA_PATTERNS` dictionary
2. **HIGH**: Reduce Vedic syllable-count confidence from 7.0 to 4.0
3. **MEDIUM**: Add missing patterns to CSV database files
4. **MEDIUM**: Handle Upajāti and other mixed-pada meters
5. **LOW**: Improve multi-line verse handling

---

## Expected Impact

If implemented correctly:

| Metric | Current | Expected |
|--------|---------|----------|
| Top-1 Accuracy | 17.4% | **70-80%** |
| Top-3 Accuracy | 19.3% | **85-90%** |
| Family-Level | 65.1% | **95%+** |

The key insight is that the model **already** correctly identifies meter families—it just needs to distinguish between specific meters within each family using pada-level L-G pattern matching.
