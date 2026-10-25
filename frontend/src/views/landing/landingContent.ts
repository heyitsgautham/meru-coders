// Copy and figures shown on the landing page.
import RigVedaImg from "../../assets/Rig_Veda.png";
import ChandovallariImg from "../../assets/Chandovallari.png";
import AtharvaVedaImg from "../../assets/Atharva_Veda.png";
import BhagavadGitaImg from "../../assets/Bhagavad_Gita.png";

export type FeatureIcon = "database" | "zap" | "book" | "sparkles";

export interface Feature {
  icon: FeatureIcon;
  title: string;
  description: string;
}

export const FEATURES: Feature[] = [
  {
    icon: "database",
    title: '1,900+ Meters',
    description: 'Comprehensive database covering Vedic, Classical, Mātrā, and Jāti meters'
  },
  {
    icon: "zap",
    title: 'Instant Analysis',
    description: 'Get meter identification results in milliseconds with confidence scores'
  },
  {
    icon: "book",
    title: 'Multi-Script',
    description: 'Supports Devanagari, IAST, and 10+ Indian regional scripts'
  },
  {
    icon: "sparkles",
    title: 'Smart Matching',
    description: 'Multi-level pattern matching with exact, pada-level, and fuzzy matching'
  }
];

export interface MeterCategory {
  name: string;
  count: number;
  description: string;
  color: string;
}

export const METER_CATEGORIES: MeterCategory[] = [
  {
    name: 'Vedic Meters',
    count: 28,
    description: 'Ancient meters from the Vedas including Gāyatrī, Triṣṭubh, and Jagatī',
    color: '#4a90d9'
  },
  {
    name: 'Sama Meters',
    count: 1629,
    description: 'Classical meters with identical patterns in all four padas',
    color: '#c75b1a'
  },
  {
    name: 'Ardhasama',
    count: 180,
    description: 'Half-equal meters with alternating pada patterns',
    color: '#7b68ee'
  },
  {
    name: 'Mātrā Meters',
    count: 9,
    description: 'Meters based on mātrā (beat) count rather than syllable patterns',
    color: '#2e8b57'
  }
];

export interface TrustedSource {
  image: string;
  title: string;
  subtitle: string;
  description: string;
  /** Zoom applied to the cover image so every book fills its card. */
  scale: number;
}

export const TRUSTED_SOURCES: TrustedSource[] = [
  {
    image: RigVedaImg,
    title: 'Rig Veda',
    subtitle: 'ऋग्वेद',
    description: 'The oldest Vedic text with diverse metrical compositions',
    scale: 1
  },
  {
    image: ChandovallariImg,
    title: 'Chandovallari',
    subtitle: 'छन्दोवल्लरी',
    description: 'Classical treatise on Sanskrit prosody and meters',
    scale: 1
  },
  {
    image: AtharvaVedaImg,
    title: 'Atharva Veda',
    subtitle: 'अथर्ववेद',
    description: 'Rich collection of hymns with varied metrical patterns',
    scale: 1
  },
  {
    image: BhagavadGitaImg,
    title: 'Bhagavad Gita',
    subtitle: 'भगवद्गीता',
    description: 'Sacred text featuring the Anuṣṭubh meter throughout',
    scale: 1.3
  }
];

export interface KeyConcept {
  symbol: string;
  symbolSize: string;
  tint: string;
  color: string;
  name: string;
  gloss: string;
  description: string;
}

export const KEY_CONCEPTS: KeyConcept[] = [
  {
    symbol: 'L',
    symbolSize: '24px',
    tint: '#e8f4fd',
    color: '#2196f3',
    name: 'Laghu (लघु)',
    gloss: 'Light / Short syllable',
    description:
      'A syllable with a short vowel (अ, इ, उ, ऋ, ऌ) not followed by a conjunct consonant or anusvāra/visarga. Counts as 1 mātrā (beat).'
  },
  {
    symbol: 'G',
    symbolSize: '24px',
    tint: '#fff3e6',
    color: '#c75b1a',
    name: 'Guru (गुरु)',
    gloss: 'Heavy / Long syllable',
    description:
      'A syllable with a long vowel (आ, ई, ऊ, ए, ऐ, ओ, औ) or a short vowel followed by a conjunct consonant, anusvāra, or visarga. Counts as 2 mātrās.'
  },
  {
    symbol: 'पद',
    symbolSize: '20px',
    tint: '#e8f5e9',
    color: '#4caf50',
    name: 'Pada (पाद)',
    gloss: 'Quarter / Foot of verse',
    description:
      'A verse is typically divided into 4 padas (quarters). The L-G pattern of each pada determines the meter. Sama meters have identical padas; Vishama meters have varying patterns.'
  }
];
