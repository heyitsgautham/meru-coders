import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';

interface BreathCycle {
  name: string;
  pattern: string;
  syllables: number;
  breaths: number;
  description: string;
}

const breathCycles: BreathCycle[] = [
  {
    name: 'Gāyatrī',
    pattern: 'GLGLGLGL',
    syllables: 8,
    breaths: 1,
    description: 'Perfect single breath cycle - most natural Vedic meter'
  },
  {
    name: 'Anuṣṭubh (Pāda 1-2)',
    pattern: 'GLGLGLGL GLGLGLGL',
    syllables: 16,
    breaths: 2,
    description: 'Comfortable two-breath pattern - Bhagavad Gita standard'
  },
  {
    name: 'Triṣṭubh (Pāda)',
    pattern: 'GLGLGLGLGLG',
    syllables: 11,
    breaths: 1,
    description: 'Extended breath for experienced chanters'
  },
  {
    name: 'Jagatī (Pāda)',
    pattern: 'GLGLGLGLGLGL',
    syllables: 12,
    breaths: 1,
    description: 'Maximum sustainable breath length'
  }
];

const BreathPatternSimulator: React.FC = () => {
  const [selectedCycle, setSelectedCycle] = useState(0);
  const [isBreathing, setIsBreathing] = useState(false);
  const [breathPhase, setBreathPhase] = useState<'inhale' | 'hold' | 'exhale'>('inhale');
  const [currentSyllable, setCurrentSyllable] = useState(-1);
  const [lungCapacity, setLungCapacity] = useState(100);

  const cycle = breathCycles[selectedCycle];
  const syllablesPerBreath = Math.ceil(cycle.syllables / cycle.breaths);

  useEffect(() => {
    if (!isBreathing) return;

    let syllableIndex = 0;
    let phase: 'inhale' | 'hold' | 'exhale' = 'inhale';
    let capacity = 100;

    const breathInterval = setInterval(() => {
      // Inhale phase (1.5s)
      if (phase === 'inhale') {
        setBreathPhase('inhale');
        capacity = Math.min(100, capacity + 20);
        setLungCapacity(capacity);
        
        setTimeout(() => {
          phase = 'hold';
          setBreathPhase('hold');
        }, 1500);
      }
      
      // Hold phase (0.5s)
      else if (phase === 'hold') {
        setTimeout(() => {
          phase = 'exhale';
          setBreathPhase('exhale');
          syllableIndex = 0;
          
          // Exhale and recite syllables
          const syllableInterval = setInterval(() => {
            if (syllableIndex < syllablesPerBreath) {
              setCurrentSyllable(syllableIndex);
              capacity = Math.max(0, capacity - (100 / syllablesPerBreath));
              setLungCapacity(capacity);
              syllableIndex++;
            } else {
              clearInterval(syllableInterval);
              setCurrentSyllable(-1);
              phase = 'inhale';
              setBreathPhase('inhale');
            }
          }, 2000 / syllablesPerBreath);
        }, 500);
      }
    }, 4000); // Full breath cycle: 4 seconds

    return () => {
      clearInterval(breathInterval);
    };
  }, [isBreathing, syllablesPerBreath]);

  const startBreathing = () => {
    setIsBreathing(true);
    setLungCapacity(0);
  };

  const stopBreathing = () => {
    setIsBreathing(false);
    setBreathPhase('inhale');
    setCurrentSyllable(-1);
    setLungCapacity(100);
  };

  return (
    <div className="space-y-6">
      {/* Cycle Selector */}
      <div className="grid md:grid-cols-2 gap-3">
        {breathCycles.map((c, idx) => (
          <button
            key={idx}
            onClick={() => {
              stopBreathing();
              setSelectedCycle(idx);
            }}
            className={`p-4 rounded-lg border-2 text-left transition-all ${
              selectedCycle === idx
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="font-semibold text-blue-900">{c.name}</div>
            <div className="text-sm text-gray-600 mt-1">
              {c.syllables} syllables • {c.breaths} breath{c.breaths > 1 ? 's' : ''}
            </div>
            <div className="text-xs text-gray-500 mt-1">{c.description}</div>
          </button>
        ))}
      </div>

      {/* Breath Visualizer */}
      <div className="bg-gradient-to-br from-blue-50 to-cyan-50 p-8 rounded-lg border-2 border-blue-300">
        <h3 className="font-bold text-xl text-center mb-6">{cycle.name} Breath Pattern</h3>
        
        {/* Lung Capacity Indicator */}
        <div className="max-w-md mx-auto mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Lung Capacity</span>
            <span className="text-sm font-bold text-blue-700">{Math.round(lungCapacity)}%</span>
          </div>
          <div className="h-8 bg-gray-200 rounded-full overflow-hidden">
            <motion.div
              animate={{ width: `${lungCapacity}%` }}
              transition={{ duration: 0.3 }}
              className={`h-full ${
                breathPhase === 'inhale' ? 'bg-green-500' :
                breathPhase === 'hold' ? 'bg-yellow-500' :
                'bg-blue-500'
              }`}
            />
          </div>
          <div className="text-center mt-2">
            <span className={`text-sm font-semibold ${
              breathPhase === 'inhale' ? 'text-green-700' :
              breathPhase === 'hold' ? 'text-yellow-700' :
              'text-blue-700'
            }`}>
              {breathPhase === 'inhale' ? '🌬️ Inhaling...' :
               breathPhase === 'hold' ? '⏸️ Holding...' :
               '🗣️ Reciting...'}
            </span>
          </div>
        </div>

        {/* Syllable Pattern Display */}
        <div className="flex flex-wrap gap-2 justify-center mb-6">
          {cycle.pattern.split(' ').map((pada, padaIdx) => (
            <div key={padaIdx} className="flex gap-1">
              {pada.split('').map((char, charIdx) => {
                const globalIdx = cycle.pattern.substring(0, cycle.pattern.indexOf(pada)).replace(/\s/g, '').length + charIdx;
                const isActive = currentSyllable === globalIdx;
                
                return (
                  <motion.div
                    key={charIdx}
                    animate={{
                      scale: isActive ? 1.3 : 1,
                      backgroundColor: isActive 
                        ? (char === 'G' ? '#3b82f6' : '#f97316')
                        : (char === 'G' ? '#dbeafe' : '#fed7aa'),
                      y: isActive ? -10 : 0
                    }}
                    transition={{ type: 'spring', stiffness: 500 }}
                    className={`w-12 h-12 rounded-lg flex items-center justify-center font-bold text-lg border-2 ${
                      char === 'G' ? 'border-blue-400' : 'border-orange-400'
                    }`}
                  >
                    {char}
                  </motion.div>
                );
              })}
            </div>
          ))}
        </div>

        {/* Breath Markers */}
        <div className="flex justify-center gap-8 mb-6">
          {Array.from({ length: cycle.breaths }).map((_, idx) => (
            <div key={idx} className="text-center">
              <div className="text-3xl mb-1">🫁</div>
              <div className="text-sm font-medium text-gray-700">Breath {idx + 1}</div>
              <div className="text-xs text-gray-600">{syllablesPerBreath} syllables</div>
            </div>
          ))}
        </div>

        {/* Control Button */}
        <div className="text-center">
          <Button
            onClick={isBreathing ? stopBreathing : startBreathing}
            size="lg"
            variant={isBreathing ? 'destructive' : 'default'}
            className="px-8"
          >
            {isBreathing ? 'Stop' : 'Start Breathing Simulation'}
          </Button>
        </div>
      </div>

      {/* Explanation */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-green-50 p-4 rounded-lg border-2 border-green-300">
          <div className="text-2xl mb-2">🌬️</div>
          <h4 className="font-semibold text-green-900 mb-1">Inhale Phase</h4>
          <p className="text-sm text-gray-700">
            Fill lungs to capacity before recitation begins
          </p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border-2 border-yellow-300">
          <div className="text-2xl mb-2">⏸️</div>
          <h4 className="font-semibold text-yellow-900 mb-1">Hold Phase</h4>
          <p className="text-sm text-gray-700">
            Brief pause to stabilize breath before speech
          </p>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg border-2 border-blue-300">
          <div className="text-2xl mb-2">🗣️</div>
          <h4 className="font-semibold text-blue-900 mb-1">Recite Phase</h4>
          <p className="text-sm text-gray-700">
            Controlled exhale while speaking syllables
          </p>
        </div>
      </div>

      {/* Real-World Connection */}
      <div className="bg-amber-50 p-6 rounded-lg border-2 border-amber-300">
        <h4 className="font-bold text-lg mb-3 text-amber-900">Why This Matters</h4>
        <ul className="space-y-2 text-gray-700">
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span>
              Ancient chanters needed meters that matched <strong>natural breath capacity</strong>
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span>
              Breaking a verse mid-breath = <strong>loss of rhythm and meaning</strong>
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span>
              Proper breath control ensures <strong>clear pronunciation</strong> and <strong>tonal accuracy</strong>
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-amber-600 font-bold">•</span>
            <span>
              L-G patterns evolved to be <strong>biologically optimal</strong> for oral transmission
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default BreathPatternSimulator;
