/**
 * DandakaResultsDisplay Component
 * Displays results for Daṇḍaka and Rājaśyāmalā Stotram identification
 *
 * Styled by styles/dandaka.css: most of the Tailwind classes this view once used
 * (gradients, text-4xl to text-8xl) are not in the precompiled index.css.
 */

import { BookOpen, Activity, TrendingUp } from 'lucide-react';
import type { DandakaModeResult } from '../types/api';
import '../styles/dandaka.css';

interface DandakaResultsDisplayProps {
  result: DandakaModeResult;
}

type Tone = 'blue' | 'green' | 'orange' | 'purple' | 'gray';

// Colour per Daṇḍaka class, used by the banner, the table badges and the legend.
const CLASSIFICATION_TONES: Record<string, Tone> = {
  'Saṃkīrṇa-daṇḍakam': 'blue',
  'Madhyama-daṇḍakam': 'green',
  'Prabandha-daṇḍakam': 'orange',
  'Ati-daṇḍakam': 'purple',
};

const CLASSIFICATION_RANGES: Record<string, string> = {
  'Saṃkīrṇa-daṇḍakam': '≤26 akṣaras per unit',
  'Madhyama-daṇḍakam': '27-51 akṣaras per unit',
  'Prabandha-daṇḍakam': '52-108 akṣaras per unit',
  'Ati-daṇḍakam': '>108 akṣaras per unit',
};

const toneOf = (classification: string): Tone => CLASSIFICATION_TONES[classification] ?? 'gray';

export function DandakaResultsDisplay({ result }: DandakaResultsDisplayProps) {
  const { text_type, dandaka, rajashyamala } = result;

  // Get overall classification - find the most common classification across units
  const getOverallClassification = () => {
    if (!dandaka || !dandaka.units || dandaka.units.length === 0) return null;

    const classificationCounts: { [key: string]: number } = {};
    dandaka.units.forEach(unit => {
      if (unit.classification) {
        classificationCounts[unit.classification] = (classificationCounts[unit.classification] || 0) + 1;
      }
    });

    let mostCommon = '';
    let maxCount = 0;
    Object.entries(classificationCounts).forEach(([classification, count]) => {
      if (count > maxCount) {
        maxCount = count;
        mostCommon = classification;
      }
    });

    return mostCommon;
  };

  const overallClassification = getOverallClassification();

  return (
    <div className="dandaka-results-container">
      {/* FINAL CLASSIFICATION BANNER */}
      {overallClassification && (
        <div className={`dandaka-banner dandaka-tone-${toneOf(overallClassification)}`}>
          <p className="dandaka-banner__label">Final classification</p>
          <h2 className="dandaka-banner__title">{overallClassification}</h2>
          <p className="dandaka-banner__range">{CLASSIFICATION_RANGES[overallClassification]}</p>
        </div>
      )}

      {/* Header */}
      <div className="dandaka-header">
        <h2>Daṇḍaka / Stotra Analysis</h2>
        <p>
          {text_type === 'rajashyamala-stotram' && 'Unmetrical Tantric Devotional Hymn'}
          {text_type === 'dandaka' && 'Long-flowing Daṇḍaka Verse'}
          {text_type === 'mixed' && 'Combined Daṇḍaka & Stotra Elements'}
          {text_type === 'unclassified' && 'Analysis Results'}
        </p>
      </div>

      {/* Rājaśyāmalā Stotram Detection */}
      {rajashyamala && rajashyamala.is_rajashyamala && (
        <section className="dandaka-card dandaka-card--purple">
          <div className="dandaka-card__title">
            <BookOpen />
            <h3>Rājaśyāmalā Stotram Identified</h3>
          </div>

          <div className="dandaka-stack">
            {/* Title Match */}
            {rajashyamala.title_match && <span className="dandaka-chip dandaka-chip--match">✓ Title Match</span>}

            {/* Confidence */}
            <div>
              <p className="dandaka-field-label">Confidence Score:</p>
              <div className="dandaka-meter">
                <div className="dandaka-meter__track">
                  <div className="dandaka-meter__fill" style={{ width: `${rajashyamala.confidence * 100}%` }} />
                </div>
                <span className="dandaka-meter__value">{(rajashyamala.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Structure Type */}
            <div>
              <p className="dandaka-field-label">Structure Type:</p>
              <span className="dandaka-tag">{rajashyamala.structure_type.replace(/-/g, ' ').toUpperCase()}</span>
            </div>

            {/* Matched Keywords */}
            {rajashyamala.matched_keywords.length > 0 && (
              <div>
                <p className="dandaka-field-label">Matched Keywords:</p>
                <div className="dandaka-chips">
                  {rajashyamala.matched_keywords.map((keyword, idx) => (
                    <span key={idx} className="dandaka-chip dandaka-chip--purple">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Semantic Markers */}
            {rajashyamala.semantic_markers.length > 0 && (
              <div>
                <p className="dandaka-field-label">Semantic Markers:</p>
                <div className="dandaka-chips">
                  {rajashyamala.semantic_markers.map((marker, idx) => (
                    <span key={idx} className="dandaka-chip dandaka-chip--amber">
                      {marker}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Important Note */}
            <div className="dandaka-note">
              <p>
                <strong>Note:</strong> Rājaśyāmalā Stotram is <strong>not a chandas</strong> and <strong>not a daṇḍaka</strong>.
                It is an unmetrical Tantric devotional hymn associated with Śyāmalā / Mātaṅgī tradition.
                No metre computation is applied - identification is based on semantic and structural markers.
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Daṇḍaka Detection */}
      {dandaka && dandaka.is_dandaka && (
        <section className="dandaka-card dandaka-card--amber">
          <div className="dandaka-card__title">
            <Activity />
            <h3>Daṇḍakam Analysis</h3>
          </div>

          {/* Summary Stats */}
          <div className="dandaka-stats">
            <div className="dandaka-stat">
              <p className="dandaka-stat__label">Total Akṣaras</p>
              <p className="dandaka-stat__value">{dandaka.total_aksaras}</p>
            </div>
            <div className="dandaka-stat">
              <p className="dandaka-stat__label">Total Virāmas</p>
              <p className="dandaka-stat__value">{dandaka.total_viramas}</p>
            </div>
            <div className="dandaka-stat">
              <p className="dandaka-stat__label">Density</p>
              <p className="dandaka-stat__value">{(dandaka.average_density * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Units Table */}
          <div className="dandaka-table-wrap">
            <table className="dandaka-table">
              <thead>
                <tr>
                  <th>Unit</th>
                  <th>Akṣaras</th>
                  <th>Virāmas</th>
                  <th>Density</th>
                  <th>Classification</th>
                </tr>
              </thead>
              <tbody>
                {dandaka.units.map((unit, idx) => (
                  <tr key={idx}>
                    <td className="dandaka-table__unit">
                      {idx + 1}. {unit.text.substring(0, 50)}...
                    </td>
                    <td className="dandaka-table__count">{unit.aksara_count}</td>
                    <td>{unit.virama_count}</td>
                    <td>{(unit.density * 100).toFixed(1)}%</td>
                    <td>
                      <span className={`dandaka-badge dandaka-tone-${toneOf(unit.classification)}`}>
                        {unit.classification}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="dandaka-legend">
            <h4>
              <TrendingUp />
              Daṇḍaka Classification Ranges:
            </h4>
            <div className="dandaka-legend__grid">
              <div><span className="dandaka-dot dandaka-tone-blue" />Saṃkīrṇa: ≤26 akṣaras</div>
              <div><span className="dandaka-dot dandaka-tone-green" />Madhyama: 27-51 akṣaras</div>
              <div><span className="dandaka-dot dandaka-tone-orange" />Prabandha: 52-108 akṣaras</div>
              <div><span className="dandaka-dot dandaka-tone-purple" />Ati-daṇḍakam: &gt;108 akṣaras</div>
            </div>
          </div>
        </section>
      )}

      {/* Unclassified State */}
      {text_type === 'unclassified' && (
        <div className="dandaka-card dandaka-card--plain">
          <p className="dandaka-unclassified">
            This text does not match Daṇḍaka or Rājaśyāmalā Stotram patterns.
            <br />
            Try using <strong>Auto</strong>, <strong>Vedic</strong>, or <strong>Classical</strong> modes for regular metre identification.
          </p>
        </div>
      )}
    </div>
  );
}
