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
  CheckCircle,
  Info,
  Users2,
  Heart,
  Award
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
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <div className="flex-shrink-0 p-3 bg-white rounded-xl text-[var(--color-primary)] shadow-sm">
                    {feature.icon}
                  </div>
                  <h3 className="font-bold text-[var(--color-text-main)]">
                    {feature.title}
                  </h3>
                </div>
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

      {/* About Us Section */}
      <div className="mb-8 p-8 bg-white rounded-2xl border-2 border-[var(--color-border-subtle)]">
        <div className="space-y-5">
          {/* About us */}
          <div className="flex items-start gap-5 p-5 rounded-xl bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-all duration-300">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <div className="flex-shrink-0 p-3 bg-white rounded-xl text-[var(--color-primary)] shadow-sm">
                  <Info className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-[var(--color-text-main)]">
                  About us
                </h3>
              </div>
              <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
                We are a team committed to making Sanskrit metrical learning simple, accurate, and accessible through interactive tools and intelligent analysis.
              </p>
            </div>
          </div>

          {/* Team */}
          <div className="flex items-start gap-5 p-5 rounded-xl bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-all duration-300">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <div className="flex-shrink-0 p-3 bg-white rounded-xl text-[var(--color-primary)] shadow-sm">
                  <Users2 className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-[var(--color-text-main)]">
                  Team
                </h3>
              </div>
              <div className="flex gap-4">
                <div className="flex flex-col items-center">
                  <img src="/team/Gautham.png" alt="Gautham Krishna S" className="w-14 h-16 object-cover rounded-md mb-1" />
                  <p className="text-center text-xs font-medium text-[var(--color-text-muted)]">Gautham Krishna S</p>
                </div>
                <div className="flex flex-col items-center">
                  <img src="/team/Kishore.png" alt="Kishore B" className="w-14 h-16 object-cover rounded-md mb-1" />
                  <p className="text-center text-xs font-medium text-[var(--color-text-muted)]">Kishore B</p>
                </div>
                <div className="flex flex-col items-center">
                  <img src="/team/Hiruthik.png" alt="Hiruthik Sudhakar" className="w-14 h-16 object-cover rounded-md mb-1" />
                  <p className="text-center text-xs font-medium text-[var(--color-text-muted)]">Hiruthik Sudhakar</p>
                </div>
                <div className="flex flex-col items-center">
                  <img src="/team/Sreevalsan.jpeg" alt="Sreevalsan V" className="w-14 h-16 object-cover rounded-md mb-1" />
                  <p className="text-center text-xs font-medium text-[var(--color-text-muted)]">Sreevalsan V</p>
                </div>
                <div className="flex flex-col items-center">
                  <img src="/team/Harevasu S.jpg" alt="Harevasu S" className="w-14 h-16 object-cover rounded-md mb-1" />
                  <p className="text-center text-xs font-medium text-[var(--color-text-muted)]">Harevasu S</p>
                </div>
                <div className="flex flex-col items-center">
                  <img src="/team/Krithika V.jpg" alt="Krithika V" className="w-14 h-16 object-cover rounded-md mb-1" />
                  <p className="text-center text-xs font-medium text-[var(--color-text-muted)]">Krithika V</p>
                </div>
              </div>
            </div>
          </div>

          {/* Contribution */}
          <div className="flex items-start gap-5 p-5 rounded-xl bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-all duration-300">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <div className="flex-shrink-0 p-3 bg-white rounded-xl text-[var(--color-primary)] shadow-sm">
                  <Award className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-[var(--color-text-main)]">
                  Contribution
                </h3>
              </div>
              <div className="text-sm text-[var(--color-text-muted)] leading-relaxed mt-3">
                <p>Gautham Krishna - Chanda Identification core engine development & Rag Engine Implementation</p>
                <p>Kishore - Backend Integration & UI/UX</p>
                <p>Hiruthik - Game development and voice to text feature implementation</p>
                <p>Sreevalasan - Dataset Curation (authentic data)</p>
                <p>Harevasu S - OCR model implementation & Chatbot implementation</p>
                <p>Krithika - Game design & implementation</p>
              </div>
            </div>
          </div>

          {/* Our commitment */}
          <div className="flex items-start gap-5 p-5 rounded-xl bg-[#fdf8f3] hover:bg-[var(--color-primary-soft)] transition-all duration-300">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <div className="flex-shrink-0 p-3 bg-white rounded-xl text-[var(--color-primary)] shadow-sm">
                  <Heart className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-[var(--color-text-main)]">
                  Our commitment
                </h3>
              </div>
              <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
                We continue refining the platform, expanding language coverage, and adding tools that improve accessibility and deepen metrical understanding.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
