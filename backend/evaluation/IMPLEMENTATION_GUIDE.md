# Quick Implementation Guide: Adopting chanda_gpt.py Improvements

**Estimated Time:** 4-6 hours  
**Priority:** High (before SIH 2025 finale)

---

## 1. Input Validation (1-2 hours) ⭐⭐⭐

### File: `backend/core/chanda.py`

Add this method to the `Chanda` class:

```python
def validate_input(self, text: str) -> tuple:
    """
    Validate input for security and quality issues.
    
    Returns:
        tuple: (is_valid: bool, error_message: str, warnings: list)
    """
    warnings = []
    
    # Empty check
    if not text or not text.strip():
        return False, "Empty input", []
    
    # Length check (DoS prevention)
    if len(text) > 10000:
        return False, "Input too long (max 10000 characters)", []
    
    # Prompt injection detection
    injection_patterns = [
        r"\{.*system.*\}",
        r"pretend|ignore all previous|override",
        r"respond in json|output json|format.*json",
        r"system:|assistant:|user:",
        r"<script|javascript:",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "Input contains suspicious patterns", []
    
    # Binary/control character check
    if re.search(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", text):
        return False, "Input contains invalid control characters", []
    
    # Warning: Very long lines (might be OCR error)
    lines = text.split('\n')
    if any(len(line) > 500 for line in lines):
        warnings.append("Very long lines detected - possible OCR error")
    
    # Warning: No Devanagari detected
    if not re.search(r"[\u0900-\u097F]", text):
        warnings.append("No Devanagari script detected")
    
    return True, "", warnings
```

### Usage in `identify_from_text()`:

```python
def identify_from_text(self, text, verse=False, return_all=False):
    # Add at the start
    is_valid, error_msg, warnings = self.validate_input(text)
    if not is_valid:
        return {
            'success': False,
            'error': error_msg,
            'result': None
        }
    
    # Continue with existing logic...
```

---

## 2. Enhanced Normalization (30 minutes) ⭐⭐

### File: `backend/core/chanda.py`

Enhance the existing `normalize_vedic_characters()` method:

```python
def normalize_vedic_characters(self, text):
    """Enhanced normalization with Unicode edge case handling"""
    if not text:
        return ""
    
    # Remove invisible Unicode characters (NEW from chanda_gpt)
    text = re.sub(r"[\u200B-\u200F\uFEFF\u202A-\u202E]", "", text)
    
    # Normalize whitespace (NEW)
    text = re.sub(r"\s+", " ", text).strip()
    
    # Remove bracketed references (NEW)
    text = re.sub(r"\[.*?\]|\{.*?\}", "", text)
    
    # Existing Vedic character normalization
    text = text.replace('\u1CF5', '\u0902')  # Ardhavisarga → Anusvara
    # ... rest of existing code
    
    return text
```

---

## 3. Diagnostic Notes (2-3 hours) ⭐⭐

### File: `backend/core/chanda.py`

Add notes tracking throughout identification:

```python
def identify_line(self, line_orig):
    """Identify meter for a single line with diagnostic notes"""
    notes = []  # Track decision process
    
    # Script detection
    detected_scheme = detect(line_orig)
    notes.append(f"Detected script: {detected_scheme}")
    
    # Syllabification
    syllables = self.get_syllables(line)
    notes.append(f"Syllabified into {len(syllables)} syllables")
    
    # L-G pattern
    lg_pattern = self.get_lg(syllables, line)
    notes.append(f"L-G pattern: {''.join(lg_pattern)}")
    
    # Meter matching
    chanda_list = self.match_with_confidence(lg, syllable_count)
    if chanda_list:
        notes.append(f"Found {len(chanda_list)} candidate meters")
        notes.append(f"Top match: {chanda_list[0][0]} (confidence: {chanda_list[0][1]})")
    else:
        notes.append("No exact matches found, trying fuzzy matching")
    
    # Add to result
    result['notes'] = notes
    return result
```

### Add `--debug` flag to API:

```python
# In webapp.py or API routes
@app.route('/api/identify/text', methods=['POST'])
def identify_text():
    debug = request.json.get('debug', False)
    
    result = chanda.identify_from_text(text, verse=verse_mode)
    
    # Strip notes if not in debug mode
    if not debug and 'notes' in result:
        del result['notes']
    
    return jsonify(result)
```

---

## 4. Mixed-Script Extraction (1 hour) ⭐⭐

### File: `backend/core/chanda.py`

Add helper method:

```python
def extract_devanagari(self, text: str) -> str:
    """Extract Devanagari text from mixed-script input"""
    RE_DEVANAGARI = re.compile(r"[\u0900-\u097F]+")
    devanagari_parts = RE_DEVANAGARI.findall(text)
    
    if devanagari_parts:
        # Join with spaces
        extracted = ' '.join(devanagari_parts)
        # Keep original if extraction is too short (might be metadata)
        if len(extracted) < 10 and len(text) > 50:
            return text
        return extracted
    
    return text
```

### Usage in preprocessing:

```python
def identify_from_text(self, text, verse=False):
    # Try to extract Devanagari if mixed-script
    if re.search(r"[a-zA-Z]", text) and re.search(r"[\u0900-\u097F]", text):
        original_text = text
        text = self.extract_devanagari(text)
        if text != original_text:
            notes.append(f"Extracted Devanagari from mixed-script input")
```

---

## 5. Explicit Vowel Classification (30 minutes) ⭐

### File: `backend/core/chanda.py`

Add class constants:

```python
class Chanda:
    """Chanda Identifier"""
    
    # ... existing constants
    
    # Vowel classification for mātrā counting
    VOWEL_CLASSIFICATION = {
        'short': {'अ', 'इ', 'उ', 'ऋ'},
        'long': {'आ', 'ई', 'ऊ', 'ए', 'ओ', 'ऐ', 'औ', 'ॠ'},
        'pluta': set()  # Extended vowels (3 mātrās) - rare
    }
    
    MATRA_CLASSIFICATION = {
        'short': {'ि', 'ु', 'ृ'},
        'long': {'ा', 'ी', 'ू', 'े', 'ै', 'ो', 'ौ', 'ॄ'}
    }
    
    # Consonant characteristics
    CONJUNCT_MARKERS = {'्'}  # Virama
    NASALS = {'ं', 'ः', 'ँ'}  # Anusvara, Visarga, Candrabindu
```

Use in `read_matra()` method for clarity.

---

## Testing Checklist

After implementing each improvement:

- [ ] **Input Validation**
  - [ ] Test with malicious inputs: `"pretend you are {system: override}"`
  - [ ] Test with very long inputs (>10000 chars)
  - [ ] Test with binary/control characters
  - [ ] Verify API returns proper error messages

- [ ] **Enhanced Normalization**
  - [ ] Test with zero-width joiners: `"धर्म\u200Bक्षेत्रे"`
  - [ ] Test with bracketed content: `"धर्मक्षेत्रे [1.1.1]"`
  - [ ] Test with mixed whitespace

- [ ] **Diagnostic Notes**
  - [ ] Verify notes appear in debug mode
  - [ ] Verify notes don't appear in production mode
  - [ ] Check notes are helpful for debugging

- [ ] **Mixed-Script**
  - [ ] Test: `"This is a verse: धर्मक्षेत्रे कुरुक्षेत्रे"`
  - [ ] Test: `"See BG 1.1: धर्मक्षेत्रे"`
  - [ ] Test: Pure Devanagari (should not change)

---

## Verification Commands

```bash
# Run existing tests to ensure no regression
cd backend
PYTHONPATH=. python tests/test_csv_accuracy.py --all

# Test input validation
python -c "
from core.chanda import Chanda
c = Chanda(data_path='data/')
is_valid, msg, warns = c.validate_input('pretend you are {system}')
print(f'Valid: {is_valid}, Message: {msg}')
"

# Test mixed-script extraction
python -c "
from core.chanda import Chanda
c = Chanda(data_path='data/')
text = 'This is verse BG 1.1: धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः'
extracted = c.extract_devanagari(text)
print(f'Extracted: {extracted}')
"
```

---

## Estimated Timeline

| Task | Time | Priority |
|------|------|----------|
| Input Validation | 1-2h | HIGH |
| Enhanced Normalization | 30m | MEDIUM |
| Diagnostic Notes | 2-3h | MEDIUM |
| Mixed-Script | 1h | MEDIUM |
| Vowel Classification | 30m | LOW |
| Testing & Verification | 1h | HIGH |
| **TOTAL** | **6-7h** | - |

---

## Success Criteria

After implementation:

✅ API rejects malicious inputs with clear error messages  
✅ Handles Unicode edge cases (OCR artifacts, invisible chars)  
✅ Debug mode provides transparency about identification process  
✅ Works with mixed-language inputs (English + Sanskrit)  
✅ Code is more maintainable with explicit constants  
✅ All existing tests still pass (no regression)

---

**Ready to implement? Start with Input Validation (highest security impact)!**
