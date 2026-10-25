"""Optional dependencies and tuning constants for the meter engine."""

# Optional ICU support for hybrid syllabization
try:
    import icu
    import regex

    ICU_AVAILABLE = True
except ImportError:
    ICU_AVAILABLE = False
    icu = None
    regex = None

# Vedic-Classical meter mappings (SIH 2025)
try:
    from .vedic_mappings import get_classical_equivalents
    from .vedic_mappings import meters_match as vedic_meters_match
    from .vedic_mappings import normalize_meter_name as normalize_vedic_meter

    VEDIC_MAPPINGS_AVAILABLE = True
except ImportError:
    VEDIC_MAPPINGS_AVAILABLE = False
    get_classical_equivalents = None
    vedic_meters_match = None
    normalize_vedic_meter = None

# size of LRU cache (currently unused - see mark_lg/transform methods)
MAX_CACHE = 1024


###############################################################################
# CONFIGURATION CONSTANTS
###############################################################################

# Confidence thresholds for meter matching (0.0 - 10.0 scale)
CONFIDENCE_EXACT_PATTERN = 10.0  # Exact L-G pattern match
CONFIDENCE_EXACT_REGEX = 9.0  # Regex pattern match with wildcards
CONFIDENCE_VEDIC_CLASSICAL_MAP = 9.8  # Vedic→Classical empirical mapping (SIH 2025)
CONFIDENCE_VEDIC_PRIMARY = 11.0  # Vedic meter by syllable count (no classical match)
CONFIDENCE_VEDIC_SECONDARY = 9.5  # Vedic meter as fallback (classical match exists)
CONFIDENCE_PADA_EXACT = 9.0  # Exact pada-level pattern match (sama)
CONFIDENCE_PADA_SIMILAR = 7.5  # Similar pada-level pattern (within tolerance)
CONFIDENCE_PADA_VEDIC_SAMA = 8.0  # Vedic meter with sama pada structure
CONFIDENCE_PADA_VEDIC_SIMILAR = 6.5  # Vedic meter with similar pada structure
CONFIDENCE_VEDIC_SYLLABLE = 6.0  # Vedic meter by syllable count alone
CONFIDENCE_SYLLABLE_COUNT = 4.0  # Fallback match by syllable count only
CONFIDENCE_FUZZY_MIN = 1.0  # Minimum fuzzy match confidence
CONFIDENCE_FUZZY_MAX = 4.0  # Maximum fuzzy match confidence

# Prose/Poetry detection thresholds
MIN_SYLLABLES_FOR_PADA = 6  # Minimum syllables for a valid pada
MIN_SYLLABLES_FOR_VERSE = 16  # Minimum for a half-shloka (2 padas of 8)
CONFIDENCE_THRESHOLD_HIGH = 9.0  # High confidence = exact pattern match
CONFIDENCE_THRESHOLD_MEDIUM = 7.0  # Medium confidence = pada/structural match

# Pattern validation thresholds
PATTERN_MATCH_TOLERANCE = 90  # Minimum match percentage (90%) for valid pattern
PATTERN_MISMATCH_MAX = 2  # Maximum L-G differences for pada matching
SYLLABLE_TOLERANCE_VEDIC = 6  # ±6 syllables for Vedic meter detection
SYLLABLE_TOLERANCE_PADA = 2  # ±2 syllables for pada-level matching

# Display and result filtering
CONFIDENCE_DISPLAY_PRIMARY = 0.8  # Show as primary if ≥80% of max confidence
CONFIDENCE_DISPLAY_ALTERNATE = 7.0  # Show as alternate if ≥7.0 confidence
MAX_FUZZY_RESULTS = 10  # Maximum fuzzy matches to return

# Input validation (for English word detection)
MIN_LENGTH_ASCII = 3  # Minimum length for romanized Sanskrit
MIN_LENGTH_DEVANAGARI = 2  # Minimum length for Devanagari script
VOWEL_RATIO_MIN = 0.15  # Minimum vowel ratio for valid Sanskrit
VOWEL_RATIO_NORMAL = 0.25  # Normal vowel ratio for Sanskrit (0.3-0.5)
ENGLISH_WORD_THRESHOLD = 0.2  # Max 20% English words allowed (no diacritics)
ENGLISH_WORD_THRESHOLD_IAST = 0.6  # Max 60% English words allowed (with IAST diacritics)

# Vedic meter detection
VEDIC_SYLLABLE_TOLERANCE_MIN = 2  # Minimum tolerance for Vedic syllable matching
VEDIC_SYLLABLE_TOLERANCE_MAX = 6  # Maximum tolerance for Vedic syllable matching
PANKTI_SIGNAL_THRESHOLD = 3.0  # Minimum score for Paṅkti meter detection

###############################################################################
