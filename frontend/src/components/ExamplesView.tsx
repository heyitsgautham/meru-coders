/**
 * ExamplesView Component
 * Displays example verses that users can click to analyze
 */

import { useEffect } from 'react';
import { Loader2, ArrowRight, BookOpen } from 'lucide-react';
import { useExamples } from '../hooks/useApi';
import type { Example } from '../types/api';

interface ExamplesViewProps {
  onSelectExample: (text: string) => void;
}

function ExampleCard({ example, onClick }: { example: Example; onClick: () => void }) {
  const lines = Array.isArray(example.lines)
    ? example.lines.filter(line => line.trim())
    : (example.text || '').split('\n').filter(line => line.trim());

  return (
    <div
      onClick={onClick}
      className="group cursor-pointer p-6 bg-white rounded-2xl border-2 border-gray-300 hover:border-orange-400 hover:shadow-xl transition-all duration-300 hover:-translate-y-1"
    >
      <h3 className="text-lg font-bold text-gray-800 group-hover:text-orange-500 transition-colors mb-4" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
        {example.meter}
      </h3>
      <div className="mb-5" style={{ fontFamily: "'Noto Sans Devanagari', sans-serif" }}>
        {lines.map((line, idx) => (
          <p key={idx} className="text-gray-800 whitespace-nowrap" style={{ fontSize: '1.1rem', lineHeight: '2' }}>
            {line}
          </p>
        ))}
      </div>
      <span className="text-sm font-semibold text-orange-500 group-hover:text-orange-600 flex items-center gap-2 transition-colors">
        Try this example
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
    onSelectExample(text);
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

      {/* Examples Grid - 3 columns */}
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
  );
}
