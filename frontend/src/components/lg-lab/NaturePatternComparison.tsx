import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Heart, Bird, Waves, Activity } from 'lucide-react';

interface NaturePattern {
  name: string;
  icon: React.ReactNode;
  lgPattern: string;
  description: string;
  frequency: string;
  color: string;
}

const naturePatterns: NaturePattern[] = [
  {
    name: 'Heartbeat',
    icon: <Heart className="w-8 h-8" />,
    lgPattern: 'LG',
    description: 'Lub-dub rhythm of cardiac cycle',
    frequency: '60-100 BPM',
    color: 'red'
  },
  {
    name: 'Bird Song',
    icon: <Bird className="w-8 h-8" />,
    lgPattern: 'LLGLG',
    description: 'Short chirps + long trills',
    frequency: 'Variable',
    color: 'emerald'
  },
  {
    name: 'Ocean Waves',
    icon: <Waves className="w-8 h-8" />,
    lgPattern: 'GLGLGLG',
    description: 'Crash and retreat cycles',
    frequency: '10-20 waves/min',
    color: 'blue'
  },
  {
    name: 'Neural Firing',
    icon: <Activity className="w-8 h-8" />,
    lgPattern: 'LGLGLG',
    description: 'Action potential bursts',
    frequency: '1-100 Hz',
    color: 'purple'
  }
];

const chandasPatterns = [
  { name: 'Gāyatrī', pattern: 'GLGLGLGL', color: 'orange' },
  { name: 'Anuṣṭubh', pattern: 'GLGLGLGL', color: 'amber' },
  { name: 'Triṣṭubh', pattern: 'GLGLGLGLGLG', color: 'green' },
  { name: 'Vasantatilaka', pattern: 'GGGLGLGGLGLGGG', color: 'pink' }
];

const NaturePatternComparison: React.FC = () => {
  const [selectedNature, setSelectedNature] = useState(0);
  const [selectedChandas, setSelectedChandas] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const nature = naturePatterns[selectedNature];
  const chandas = chandasPatterns[selectedChandas];

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; border: string; text: string }> = {
      red: { bg: 'bg-red-100', border: 'border-red-400', text: 'text-red-700' },
      emerald: { bg: 'bg-emerald-100', border: 'border-emerald-400', text: 'text-emerald-700' },
      blue: { bg: 'bg-blue-100', border: 'border-blue-400', text: 'text-blue-700' },
      purple: { bg: 'bg-purple-100', border: 'border-purple-400', text: 'text-purple-700' },
      orange: { bg: 'bg-orange-100', border: 'border-orange-400', text: 'text-orange-700' },
      amber: { bg: 'bg-amber-100', border: 'border-amber-400', text: 'text-amber-700' },
      green: { bg: 'bg-green-100', border: 'border-green-400', text: 'text-green-700' },
      pink: { bg: 'bg-pink-100', border: 'border-pink-400', text: 'text-pink-700' }
    };
    return colors[color] || colors.blue;
  };

  const renderPattern = (pattern: string, color: string, label: string) => {
    const colors = getColorClasses(color);
    
    return (
      <div className="space-y-2">
        <div className="text-sm font-medium text-gray-700 text-center">{label}</div>
        <div className="flex gap-1 justify-center flex-wrap">
          {pattern.split('').map((char, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0 }}
              animate={{ 
                opacity: 1, 
                scale: isAnimating ? [1, 1.2, 1] : 1,
                y: isAnimating ? [0, -10, 0] : 0
              }}
              transition={{ 
                delay: idx * 0.1,
                repeat: isAnimating ? Infinity : 0,
                repeatDelay: pattern.length * 0.1
              }}
              className={`w-10 h-10 rounded flex items-center justify-center font-bold border-2 ${
                char === 'G' ? colors.bg + ' ' + colors.border : 'bg-gray-100 border-gray-300'
              }`}
            >
              <span className={char === 'G' ? colors.text : 'text-gray-600'}>{char}</span>
            </motion.div>
          ))}
        </div>
      </div>
    );
  };

  const calculateSimilarity = (pattern1: string, pattern2: string): number => {
    const len = Math.min(pattern1.length, pattern2.length);
    let matches = 0;
    for (let i = 0; i < len; i++) {
      if (pattern1[i] === pattern2[i]) matches++;
    }
    return Math.round((matches / len) * 100);
  };

  const similarity = calculateSimilarity(nature.lgPattern, chandas.pattern);

  return (
    <div className="space-y-6">
      {/* Nature Pattern Selector */}
      <div>
        <h3 className="font-bold text-lg mb-3">Select a Natural Rhythm</h3>
        <div className="grid md:grid-cols-4 gap-3">
          {naturePatterns.map((p, idx) => {
            const colors = getColorClasses(p.color);
            return (
              <button
                key={idx}
                onClick={() => setSelectedNature(idx)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedNature === idx
                    ? colors.border + ' ' + colors.bg
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className={`flex justify-center mb-2 ${selectedNature === idx ? colors.text : 'text-gray-600'}`}>
                  {p.icon}
                </div>
                <div className="font-semibold text-sm text-center">{p.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Chandas Pattern Selector */}
      <div>
        <h3 className="font-bold text-lg mb-3">Select a Chandas Meter</h3>
        <div className="grid md:grid-cols-4 gap-3">
          {chandasPatterns.map((p, idx) => {
            const colors = getColorClasses(p.color);
            return (
              <button
                key={idx}
                onClick={() => setSelectedChandas(idx)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedChandas === idx
                    ? colors.border + ' ' + colors.bg
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold text-sm text-center">{p.name}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison View */}
      <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-8 rounded-lg border-2 border-gray-300">
        <div className="grid md:grid-cols-2 gap-8 mb-6">
          {/* Nature Pattern */}
          <div className={`p-6 rounded-lg border-2 ${getColorClasses(nature.color).bg} ${getColorClasses(nature.color).border}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={getColorClasses(nature.color).text}>
                {nature.icon}
              </div>
              <div>
                <h4 className="font-bold text-lg">{nature.name}</h4>
                <p className="text-sm text-gray-600">{nature.description}</p>
              </div>
            </div>
            <div className="bg-white p-3 rounded mb-3">
              <div className="text-xs text-gray-600 mb-1">Frequency</div>
              <div className="font-semibold">{nature.frequency}</div>
            </div>
            {renderPattern(nature.lgPattern, nature.color, 'Natural Pattern')}
          </div>

          {/* Chandas Pattern */}
          <div className={`p-6 rounded-lg border-2 ${getColorClasses(chandas.color).bg} ${getColorClasses(chandas.color).border}`}>
            <div className="mb-4">
              <h4 className="font-bold text-lg">{chandas.name}</h4>
              <p className="text-sm text-gray-600">Classical Sanskrit meter</p>
            </div>
            <div className="bg-white p-3 rounded mb-3">
              <div className="text-xs text-gray-600 mb-1">Syllables</div>
              <div className="font-semibold">{chandas.pattern.length}</div>
            </div>
            {renderPattern(chandas.pattern, chandas.color, 'Chandas Pattern')}
          </div>
        </div>

        {/* Similarity Score */}
        <div className="bg-white p-6 rounded-lg border-2 border-gray-300 mb-4">
          <div className="flex items-center justify-between mb-3">
            <span className="font-bold text-lg">Pattern Similarity</span>
            <span className="text-3xl font-bold text-green-600">{similarity}%</span>
          </div>
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${similarity}%` }}
              transition={{ duration: 1, delay: 0.3 }}
              className="h-full bg-gradient-to-r from-green-500 to-emerald-500"
            />
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Based on matching L-G positions in the first {Math.min(nature.lgPattern.length, chandas.pattern.length)} syllables
          </p>
        </div>

        {/* Animation Control */}
        <div className="text-center">
          <button
            onClick={() => setIsAnimating(!isAnimating)}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-purple-600 transition-all"
          >
            {isAnimating ? 'Stop Animation' : 'Animate Patterns'}
          </button>
        </div>
      </div>

      {/* Explanation Cards */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-emerald-50 p-6 rounded-lg border-2 border-emerald-300">
          <h4 className="font-bold text-lg mb-3 text-emerald-900">Why Binary Rhythms?</h4>
          <p className="text-gray-700 text-sm leading-relaxed">
            Nature loves binary oscillations because they're <strong>energetically efficient</strong>. 
            From heartbeats to ocean waves, short-long patterns create stable, self-sustaining cycles. 
            Sanskrit chandas evolved to mirror these universal rhythms.
          </p>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg border-2 border-blue-300">
          <h4 className="font-bold text-lg mb-3 text-blue-900">Resonance & Memory</h4>
          <p className="text-gray-700 text-sm leading-relaxed">
            When chandas patterns match natural rhythms, they create <strong>cognitive resonance</strong>. 
            Your brain recognizes these patterns from the world around you, making them easier to remember, 
            recite, and internalize.
          </p>
        </div>
      </div>

      {/* Key Insight */}
      <div className="bg-gradient-to-r from-amber-100 to-orange-100 p-6 rounded-lg border-2 border-orange-400">
        <div className="flex items-start gap-4">
          <div className="text-4xl">🌟</div>
          <div>
            <h4 className="font-bold text-xl text-orange-900 mb-2">The Deep Connection</h4>
            <p className="text-gray-800 leading-relaxed">
              Ancient Sanskrit poets didn't <em>invent</em> these patterns — they <em>discovered</em> them 
              by listening to the rhythms already present in nature, the human body, and consciousness itself. 
              Chandas are <strong>nature's mathematics expressed through sound</strong>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NaturePatternComparison;
