/**
 * ExamplesView Component
 * Displays example verses that users can click to analyze
 */

import { useEffect } from 'react';
import { Loader2, ArrowRight, BookOpen } from 'lucide-react';
import { useExamples } from '../hooks/useApi';
import type { Example } from '../types/api';

interface ExamplesViewProps {
  onSelectExample: (text: string, mode?: string) => void;
}

function ExampleCard({ example, onClick, isDandaka = false }: { example: Example; onClick: () => void; isDandaka?: boolean }) {
  const lines = Array.isArray(example.lines)
    ? example.lines.filter(line => line.trim())
    : (example.text || '').split('\n').filter(line => line.trim());

  // For dandaka examples, show first 2 lines as preview
  const displayLines = isDandaka ? lines.slice(0, 2) : lines;

  return (
    <div
      onClick={onClick}
      className="group cursor-pointer p-6 bg-white rounded-2xl border-2 border-gray-300 hover:border-orange-400 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
    >
      <h3 className="text-lg font-bold text-gray-800 group-hover:text-orange-500 transition-colors mb-4" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
        {example.meter}
      </h3>
      <div className="mb-5" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
        {displayLines.map((line, idx) => (
          <p key={idx} className="text-gray-800 overflow-hidden text-ellipsis" style={{ fontSize: '1rem', lineHeight: '1.8' }}>
            {line}
          </p>
        ))}
        {isDandaka && lines.length > 2 && (
          <p className="text-gray-500 italic text-sm mt-2">+ {lines.length - 2} more line{lines.length - 2 > 1 ? 's' : ''}</p>
        )}
      </div>
      <span className="text-sm font-semibold text-orange-500 group-hover:text-orange-600 flex items-center gap-2 transition-colors">
        {isDandaka ? 'Analyze this dandaka' : 'Analyze this verse'}
        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
      </span>
    </div>
  );
}

export function ExamplesView({ onSelectExample }: ExamplesViewProps) {
  const { examples, loading, error, loadExamples, loaded } = useExamples();

  // Load examples when component mounts
  useEffect(() => {
    if (!loaded) {
      loadExamples();
    }
  }, [loaded, loadExamples]);

  const handleSelect = (example: Example) => {
    const text = Array.isArray(example.lines)
      ? example.lines.filter(line => line.trim()).join('\n')
      : (example.text || '');
    onSelectExample(text, example.mode);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="w-8 h-8 text-[var(--color-primary)] animate-spin mb-4" />
        <p className="text-[var(--color-text-muted)]">Loading examples...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <BookOpen className="w-8 h-8 text-red-500" />
        </div>
        <h3 className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
          Failed to Load Examples
        </h3>
        <p className="text-[var(--color-text-muted)] mb-4">{error}</p>
        <button
          onClick={loadExamples}
          className="px-6 py-2.5 bg-[var(--color-primary)] text-white rounded-full text-sm font-medium hover:bg-[var(--color-primary-dark)] transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (examples.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <BookOpen className="w-8 h-8 text-amber-500" />
        </div>
        <h3 className="text-lg font-semibold text-[var(--color-text-main)] mb-2">
          No Examples Available
        </h3>
        <p className="text-[var(--color-text-muted)]">
          Check back later for example verses.
        </p>
      </div>
    );
  }

  // Dandaka examples - one for each classification (ACCURATE)
  const dandakaExamples: Example[] = [
    {
      meter: 'संकीर्ण-दण्डकम् (Saṃkīrṇa-daṇḍakam)',
      text: 'रामो राजमणिः सदा विजयते रामं रमेशं भजे।',
      lines: ['रामो राजमणिः सदा विजयते रामं रमेशं भजे।'],
      mode: 'dandaka'
    },
    {
      meter: 'मध्यम-दण्डकम् (Madhyama-daṇḍakam)',
      text: 'यस्मिन् जातो रामः सर्वेषां लोकानां हितकरः सत्यप्रतिज्ञः धर्मात्मा स राजा दशरथः।',
      lines: [
        'यस्मिन् जातो रामः सर्वेषां लोकानां हितकरः सत्यप्रतिज्ञः धर्मात्मा स राजा दशरथः।'
      ],
      mode: 'dandaka'
    },
    {
      meter: 'प्रबन्ध-दण्डकम् (Prabandha-daṇḍakam)',
      text: 'तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य।',
      lines: [
        'तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य।'
      ],
      mode: 'dandaka'
    },
    {
      meter: 'अति-दण्डकम् (Ati-daṇḍakam)',
      text: 'तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य चकास चामीकरशैलकूटनिष्क्रान्तशाखं महतः पतत्रं स्फुरत्पाटलाभोगवपुः प्रभायां दधद्रोचिषां संहतिं रोचमानं तमः सद्य आर्द्रालिगोप्यम्।',
      lines: [
        'तस्याः प्रभावादिव धूमजालेरन्तर्हितः कौशिकसप्तरश्मिः महार्णवोर्मिस्फुरदाविलत्वाद्बभूव तेजस्तिमिरेण मिश्रः क्षणेन गृध्रप्रतिमानभःस्थच्छायातपत्रं जगतीश्वरस्य चकास चामीकरशैलकूटनिष्क्रान्तशाखं महतः पतत्रं स्फुरत्पाटलाभोगवपुः प्रभायां दधद्रोचिषां संहतिं रोचमानं तमः सद्य आर्द्रालिगोप्यम्।'
      ],
      mode: 'dandaka'
    }
  ];

  return (
    <div className="animate-fadeIn px-6 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-[var(--color-text-main)] mb-4">
          Example Verses
        </h1>
        <p className="text-lg text-[var(--color-text-muted)]">
          Click on any example to analyze its meter
        </p>
      </div>

      {/* Classical Meters Section */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-[var(--color-text-main)] mb-6 flex items-center gap-3">
          <BookOpen className="w-6 h-6 text-orange-500" />
          Classical Meters
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {examples.map((example, index) => (
            <ExampleCard
              key={index}
              example={example}
              onClick={() => handleSelect(example)}
            />
          ))}
        </div>
      </div>

      {/* Dandaka Examples Section */}
      <div>
        <h2 className="text-2xl font-bold text-[var(--color-text-main)] mb-4 flex items-center gap-3">
          {/* Inline styles: the gradient utilities are missing from the precompiled index.css. */}
          <div
            className="flex items-center justify-center"
            style={{
              flexShrink: 0,
              width: '32px',
              height: '32px',
              borderRadius: '9999px',
              background: 'linear-gradient(135deg, #fbbf24, #f97316, #ef4444)',
              boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
            }}
          >
            <span style={{ color: '#fff', fontSize: '14px', fontWeight: 700 }}>द</span>
          </div>
          Daṇḍaka Examples
        </h2>
        <p className="text-gray-600 mb-6 ml-11">
          Unmetrical compositions - System will classify the entire text as one of four types
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {dandakaExamples.map((example, index) => (
            <ExampleCard
              key={`dandaka-${index}`}
              example={example}
              onClick={() => handleSelect(example)}
              isDandaka={true}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
