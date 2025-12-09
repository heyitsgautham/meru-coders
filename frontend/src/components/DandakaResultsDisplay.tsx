/**
 * DandakaResultsDisplay Component
 * Displays results for Daṇḍaka and Rājaśyāmalā Stotram identification
 */

import { BookOpen, Activity, TrendingUp } from 'lucide-react';
import type { DandakaModeResult } from '../types/api';

interface DandakaResultsDisplayProps {
  result: DandakaModeResult;
}

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

  // Color coding for Daṇḍaka classifications
  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'Saṃkīrṇa-daṇḍakam':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'Madhyama-daṇḍakam':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'Prabandha-daṇḍakam':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'Ati-daṇḍakam':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getClassificationGradient = (classification: string) => {
    switch (classification) {
      case 'Saṃkīrṇa-daṇḍakam':
        return 'from-blue-500 to-blue-700';
      case 'Madhyama-daṇḍakam':
        return 'from-green-500 to-green-700';
      case 'Prabandha-daṇḍakam':
        return 'from-orange-500 to-orange-700';
      case 'Ati-daṇḍakam':
        return 'from-purple-500 to-purple-700';
      default:
        return 'from-gray-500 to-gray-700';
    }
  };

  return (
    <div className="dandaka-results-container p-12 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl shadow-lg">
      {/* FINAL CLASSIFICATION BANNER */}
      {overallClassification && (
        <div className={`mb-10 p-8 bg-gradient-to-r ${getClassificationGradient(overallClassification)} rounded-2xl shadow-2xl text-white text-center transform hover:scale-105 transition-transform duration-300`}>
          <p className="text-3xl font-semibold mb-2 opacity-90">FINAL CLASSIFICATION</p>
          <h2 className="text-8xl font-bold mb-3">{overallClassification}</h2>
          <p className="text-4xl opacity-90">
            {overallClassification === 'Saṃkīrṇa-daṇḍakam' && '≤26 akṣaras per unit'}
            {overallClassification === 'Madhyama-daṇḍakam' && '27-51 akṣaras per unit'}
            {overallClassification === 'Prabandha-daṇḍakam' && '52-108 akṣaras per unit'}
            {overallClassification === 'Ati-daṇḍakam' && '>108 akṣaras per unit'}
          </p>
        </div>
      )}

      {/* Header */}
      <div className="mb-12 text-center">
        <h2 className="text-7xl font-bold text-amber-900 mb-3">
          Daṇḍaka / Stotra Analysis
        </h2>
        <p className="text-4xl text-amber-700">
          {text_type === 'rajashyamala-stotram' && 'Unmetrical Tantric Devotional Hymn'}
          {text_type === 'dandaka' && 'Long-flowing Daṇḍaka Verse'}
          {text_type === 'mixed' && 'Combined Daṇḍaka & Stotra Elements'}
          {text_type === 'unclassified' && 'Analysis Results'}
        </p>
      </div>

      {/* Rājaśyāmalā Stotram Detection */}
      {rajashyamala && rajashyamala.is_rajashyamala && (
        <div className="mb-10 p-8 bg-white rounded-xl shadow-md border-2 border-purple-300">
          <div className="flex items-center gap-4 mb-6">
            <BookOpen className="w-14 h-14 text-purple-600" />
            <h3 className="text-5xl font-bold text-purple-900">
              Rājaśyāmalā Stotram Identified
            </h3>
          </div>

          <div className="space-y-6">
            {/* Title Match */}
            {rajashyamala.title_match && (
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-2xl font-semibold">
                  ✓ Title Match
                </span>
              </div>
            )}

            {/* Confidence */}
            <div>
              <p className="text-3xl font-semibold text-gray-700 mb-3">Confidence Score:</p>
              <div className="flex items-center gap-4">
                <div className="flex-1 h-10 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-400 to-purple-600 transition-all duration-500"
                    style={{ width: `${rajashyamala.confidence * 100}%` }}
                  />
                </div>
                <span className="font-bold text-purple-900 text-3xl">
                  {(rajashyamala.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Structure Type */}
            <div>
              <p className="text-3xl font-semibold text-gray-700 mb-3">Structure Type:</p>
              <span className="inline-block px-5 py-2.5 bg-purple-50 text-purple-800 rounded-lg border border-purple-200 font-medium text-3xl">
                {rajashyamala.structure_type.replace(/-/g, ' ').toUpperCase()}
              </span>
            </div>

            {/* Matched Keywords */}
            {rajashyamala.matched_keywords.length > 0 && (
              <div>
                <p className="text-3xl font-semibold text-gray-700 mb-3">Matched Keywords:</p>
                <div className="flex flex-wrap gap-2.5">
                  {rajashyamala.matched_keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="px-4 py-1.5 bg-purple-100 text-purple-800 rounded-full text-3xl border border-purple-200"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Semantic Markers */}
            {rajashyamala.semantic_markers.length > 0 && (
              <div>
                <p className="text-3xl font-semibold text-gray-700 mb-3">Semantic Markers:</p>
                <div className="flex flex-wrap gap-2.5">
                  {rajashyamala.semantic_markers.map((marker, idx) => (
                    <span
                      key={idx}
                      className="px-4 py-1.5 bg-amber-100 text-amber-800 rounded-full text-3xl border border-amber-200"
                    >
                      {marker}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Important Note */}
            <div className="mt-6 p-5 bg-amber-50 border-l-4 border-amber-400 rounded">
              <p className="text-3xl text-amber-900">
                <strong>Note:</strong> Rājaśyāmalā Stotram is <strong>not a chandas</strong> and <strong>not a daṇḍaka</strong>.
                It is an unmetrical Tantric devotional hymn associated with Śyāmalā / Mātaṅgī tradition.
                No metre computation is applied - identification is based on semantic and structural markers.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Daṇḍaka Detection */}
      {dandaka && dandaka.is_dandaka && (
        <div className="p-8 bg-white rounded-xl shadow-md border-2 border-amber-300">
          <div className="flex items-center gap-4 mb-6">
            <Activity className="w-14 h-14 text-amber-600" />
            <h3 className="text-5xl font-bold text-amber-900">
              Daṇḍakam Analysis
            </h3>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-6 mb-8">
            <div className="p-6 bg-amber-50 rounded-lg border border-amber-200 text-center">
              <p className="text-3xl text-amber-700 mb-2">Total Akṣaras</p>
              <p className="text-6xl font-bold text-amber-900">{dandaka.total_aksaras}</p>
            </div>
            <div className="p-6 bg-amber-50 rounded-lg border border-amber-200 text-center">
              <p className="text-3xl text-amber-700 mb-2">Total Virāmas</p>
              <p className="text-6xl font-bold text-amber-900">{dandaka.total_viramas}</p>
            </div>
            <div className="p-6 bg-amber-50 rounded-lg border border-amber-200 text-center">
              <p className="text-3xl text-amber-700 mb-2">Density</p>
              <p className="text-6xl font-bold text-amber-900">{(dandaka.average_density * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Units Table */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-amber-100">
                  <th className="px-5 py-4 text-left text-3xl font-semibold text-amber-900 border-b-2 border-amber-300">
                    Unit
                  </th>
                  <th className="px-5 py-4 text-center text-3xl font-semibold text-amber-900 border-b-2 border-amber-300">
                    Akṣaras
                  </th>
                  <th className="px-5 py-4 text-center text-3xl font-semibold text-amber-900 border-b-2 border-amber-300">
                    Virāmas
                  </th>
                  <th className="px-5 py-4 text-center text-3xl font-semibold text-amber-900 border-b-2 border-amber-300">
                    Density
                  </th>
                  <th className="px-5 py-4 text-center text-3xl font-semibold text-amber-900 border-b-2 border-amber-300">
                    Classification
                  </th>
                </tr>
              </thead>
              <tbody>
                {dandaka.units.map((unit, idx) => (
                  <tr key={idx} className="hover:bg-amber-50 transition-colors">
                    <td className="px-5 py-4 text-3xl text-gray-700 border-b border-amber-200">
                      {idx + 1}. {unit.text.substring(0, 50)}...
                    </td>
                    <td className="px-5 py-4 text-center text-3xl font-semibold text-gray-900 border-b border-amber-200">
                      {unit.aksara_count}
                    </td>
                    <td className="px-5 py-4 text-center text-3xl text-gray-700 border-b border-amber-200">
                      {unit.virama_count}
                    </td>
                    <td className="px-5 py-4 text-center text-3xl text-gray-700 border-b border-amber-200">
                      {(unit.density * 100).toFixed(1)}%
                    </td>
                    <td className="px-5 py-4 text-center border-b border-amber-200">
                      <span className={`px-4 py-1.5 rounded-full text-2xl font-semibold border ${getClassificationColor(unit.classification)}`}>
                        {unit.classification}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="mt-8 p-6 bg-gray-50 rounded-lg">
            <h4 className="text-3xl font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <TrendingUp className="w-8 h-8" />
              Daṇḍaka Classification Ranges:
            </h4>
            <div className="grid grid-cols-2 gap-3 text-2xl">
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 rounded-full bg-blue-400" />
                <span>Saṃkīrṇa: ≤26 akṣaras</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 rounded-full bg-green-400" />
                <span>Madhyama: 27-51 akṣaras</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 rounded-full bg-orange-400" />
                <span>Prabandha: 52-108 akṣaras</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-4 h-4 rounded-full bg-purple-400" />
                <span>Ati-daṇḍakam: &gt;108 akṣaras</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Unclassified State */}
      {text_type === 'unclassified' && (
        <div className="p-8 bg-white rounded-xl shadow-md border-2 border-gray-300 text-center">
          <p className="text-3xl text-gray-600">
            This text does not match Daṇḍaka or Rājaśyāmalā Stotram patterns.
            <br />
            Try using <strong>Auto</strong>, <strong>Vedic</strong>, or <strong>Classical</strong> modes for regular metre identification.
          </p>
        </div>
      )}
    </div>
  );
}
