/**
 * UpcomingView Component
 * Future Implementation section showcasing upcoming features
 */

import { 
  Eye, 
  Network, 
  Layers, 
  FileCode, 
  GitCompare
} from 'lucide-react';

export function UpcomingView() {
  const upcomingFeatures = [
    {
      icon: <Eye className="w-5 h-5" />,
      title: 'OUR VISION',
      description: 'To make metrical learning accessible across major Indian languages.'
    },
    {
      icon: <Network className="w-5 h-5" />,
      title: 'CROSS-LANGUAGE PROSODY FRAMEWORK',
      description: 'Build a unified framework that supports adding new language-specific prosody engines, enabling smooth expansion beyond Sanskrit.'
    },
    {
      icon: <Layers className="w-5 h-5" />,
      title: 'MODULAR ARCHITECTURE FOR NEW LANGUAGES',
      description: 'We design the platform so each language can exist as a separate module, making future expansions easy and consistent.'
    },
    {
      icon: <FileCode className="w-5 h-5" />,
      title: 'TAMIL PROSODY ENGINE',
      description: 'Introduce an independent module for Tamil poetic meters (யாப்பு) with support for Asai, Seer, Yāppu, and Venpa classification.'
    },
    {
      icon: <GitCompare className="w-5 h-5" />,
      title: 'TAMIL–SANSKRIT COMPARISON MODULE',
      description: 'Offer a comparison module that highlights structural differences between Tamil Yāppu and Sanskrit Chandas for cross-linguistic learning.'
    }
  ];

  return (
    <div className="animate-fadeIn max-w-3xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-[var(--color-text-main)] mb-4">
          Future Implementation
        </h1>
      </div>

      {/* Upcoming Features Section */}
      <div className="mb-8 p-8 bg-white rounded-2xl border-2 border-[var(--color-border-subtle)]">
        <div className="space-y-5">
          {upcomingFeatures.map((feature, index) => (
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
    </div>
  );
}
