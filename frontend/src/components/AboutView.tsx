/**
 * AboutView Component
 * About page with feature list and usage instructions
 */

import { 
  BookOpen, 
  Image, 
  FileText, 
  Languages, 
  Sparkles, 
  CheckCircle
} from 'lucide-react';

export function AboutView() {
  const features = [
    {
      icon: <BookOpen className="w-5 h-5" />,
      title: 'Identify meters from Sanskrit text',
      description: 'Analyze Sanskrit verses to identify their prosodic meters (छन्द)'
    },
    {
      icon: <Image className="w-5 h-5" />,
      title: 'OCR support for images',
      description: 'Extract text from images containing Sanskrit text using Tesseract or Google OCR'
    },
    {
      icon: <FileText className="w-5 h-5" />,
      title: 'Batch processing of text files',
      description: 'Upload text files for bulk meter analysis'
    },
    {
      icon: <Languages className="w-5 h-5" />,
      title: 'Multiple transliteration schemes',
      description: 'Support for Devanagari, IAST, ITRANS, and more'
    },
    {
      icon: <Sparkles className="w-5 h-5" />,
      title: 'Fuzzy matching',
      description: 'Identify meters even when text has minor variations or errors'
    }
  ];

  const steps = [
    'Choose an input method (Text, Image, or File)',
    'Enter or upload your Sanskrit content',
    'Select analysis mode and output scheme',
    'Click analyze to identify the meter'
  ];

  return (
    <div className="animate-fadeIn max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-[var(--color-text-main)] mb-4">
          About
        </h1>
        <p className="text-[var(--color-text-muted)] text-lg leading-relaxed">
          The Sanskrit Meter Identification System helps analyze Sanskrit verses 
          and identify their meters (छन्द).
        </p>
      </div>

      {/* Features Section */}
      <div className="mb-8 p-8 bg-white rounded-2xl border-2 border-[var(--color-border-subtle)]">
        <h2 className="text-xl font-bold text-[var(--color-text-main)] mb-8 flex items-center gap-3">
          <div className="p-2.5 bg-[var(--color-primary-soft)] rounded-xl">
            <Sparkles className="w-5 h-5 text-[var(--color-primary)]" />
          </div>
          Features
        </h2>
        <div className="space-y-5">
          {features.map((feature, index) => (
            <div
              key={index}
              className="flex items-start gap-5 p-5 rounded-xl bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-all duration-300"
            >
              <div className="flex-shrink-0 p-3 bg-white rounded-xl text-[var(--color-primary)] shadow-sm">
                {feature.icon}
              </div>
              <div>
                <h3 className="font-bold text-[var(--color-text-main)] mb-1.5">
                  {feature.title}
                </h3>
                <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* How to Use Section */}
      <div className="mb-8 p-8 bg-white rounded-2xl border-2 border-[var(--color-border-subtle)]">
        <h2 className="text-xl font-bold text-[var(--color-text-main)] mb-8 flex items-center gap-3">
          <div className="p-2.5 bg-[var(--color-primary-soft)] rounded-xl">
            <BookOpen className="w-5 h-5 text-[var(--color-primary)]" />
          </div>
          How to Use
        </h2>
        <ol className="space-y-4">
          {steps.map((step, index) => (
            <li key={index} className="flex items-center gap-5 p-5 rounded-xl bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-colors">
              <span className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-primary-dark)] text-white text-base font-bold flex items-center justify-center shadow-md">
                {index + 1}
              </span>
              <span className="text-[var(--color-text-main)] font-medium">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Technical Details Section */}
      <div className="mb-8 p-8 bg-white rounded-2xl border-2 border-[var(--color-border-subtle)]">
        <h2 className="text-xl font-bold text-[var(--color-text-main)] mb-8 flex items-center gap-3">
          <div className="p-2.5 bg-[var(--color-primary-soft)] rounded-xl">
            <CheckCircle className="w-5 h-5 text-[var(--color-primary)]" />
          </div>
          Technical Details
        </h2>
        <div className="space-y-5">
          <p className="text-[var(--color-text-main)] leading-relaxed text-base">
            This application uses advanced algorithms for meter identification, 
            including fuzzy sequence matching and syllable analysis. It supports 
            multiple Indian language scripts through OCR integration.
          </p>
          <p className="text-sm text-[var(--color-text-muted)] leading-relaxed pt-5 border-t-2 border-[var(--color-border-subtle)]">
            Built with React, TypeScript, and Tailwind CSS. Backend powered by 
            Python/Flask with advanced Sanskrit prosody analysis.
          </p>
        </div>
      </div>
    </div>
  );
}
