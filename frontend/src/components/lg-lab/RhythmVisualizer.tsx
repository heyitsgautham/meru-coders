import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface RhythmPattern {
  name: string;
  pattern: string;
  matra: number[];
  description: string;
}

const rhythmPatterns: RhythmPattern[] = [
  {
    name: 'Gayatri (8 syllables)',
    pattern: 'GLGLGLGL',
    matra: [2, 1, 2, 1, 2, 1, 2, 1],
    description: 'Basic Vedic meter with simple alternation'
  },
  {
    name: 'Anuṣṭubh (8 syllables)',
    pattern: 'GLGLGLGL',
    matra: [2, 1, 2, 1, 2, 1, 2, 1],
    description: 'Most common classical meter (like Bhagavad Gita)'
  },
  {
    name: 'Vasantatilaka (14 syllables)',
    pattern: 'GGGLGLGGLGLGGG',
    matra: [2, 2, 2, 1, 2, 1, 2, 2, 1, 2, 1, 2, 2, 2],
    description: 'Spring blossom - flowing romantic meter'
  },
  {
    name: 'Mandākrāntā (17 syllables)',
    pattern: 'GGGGGLLGLGLGLGGGG',
    matra: [2, 2, 2, 2, 2, 1, 1, 2, 1, 2, 1, 2, 1, 2, 2, 2, 2],
    description: 'Slow-moving - majestic and dignified'
  }
];

const RhythmVisualizer: React.FC = () => {
  const [selectedPattern, setSelectedPattern] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentBeat, setCurrentBeat] = useState(-1);
  const [tempo, setTempo] = useState(120); // BPM
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const pattern = rhythmPatterns[selectedPattern];

  // Initialize Web Audio API
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Play a beep sound
  const playBeep = (frequency: number, duration: number) => {
    if (!audioContextRef.current) return;

    const ctx = audioContextRef.current;
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + duration);
  };

  // Start/stop rhythm playback
  const togglePlay = () => {
    if (isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsPlaying(false);
      setCurrentBeat(-1);
    } else {
      setIsPlaying(true);
      let beatIndex = 0;
      
      intervalRef.current = setInterval(() => {
        const lgChar = pattern.pattern[beatIndex];
        const matra = pattern.matra[beatIndex];
        
        // Higher pitch for Guru, lower for Laghu
        const frequency = lgChar === 'G' ? 600 : 400;
        const duration = (60 / tempo) * matra * 0.3;
        
        playBeep(frequency, duration);
        setCurrentBeat(beatIndex);
        
        beatIndex++;
        if (beatIndex >= pattern.pattern.length) {
          beatIndex = 0;
        }
      }, (60 / tempo) * 1000);
    }
  };

  const reset = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPlaying(false);
    setCurrentBeat(-1);
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Pattern Selector */}
      <div className="bg-white p-4 rounded-lg border-2 border-purple-200">
        <h3 className="font-bold text-lg mb-3">Select a Meter</h3>
        <div className="grid md:grid-cols-2 gap-3">
          {rhythmPatterns.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                reset();
                setSelectedPattern(idx);
              }}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                selectedPattern === idx
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-200 hover:border-purple-300'
              }`}
            >
              <div className="font-semibold text-purple-900">{p.name}</div>
              <div className="text-sm text-gray-600 mt-1">{p.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Rhythm Visualizer */}
      <div className="bg-gradient-to-br from-purple-50 to-indigo-50 p-6 rounded-lg border-2 border-purple-300">
        <h3 className="font-bold text-lg mb-4">{pattern.name}</h3>
        
        {/* Visual Pattern Display */}
        <div className="flex flex-wrap gap-2 justify-center mb-6">
          {pattern.pattern.split('').map((char, idx) => {
            const isActive = currentBeat === idx;
            const matra = pattern.matra[idx];
            
            return (
              <motion.div
                key={idx}
                animate={{
                  scale: isActive ? 1.2 : 1,
                  backgroundColor: isActive 
                    ? (char === 'G' ? '#3b82f6' : '#f97316')
                    : (char === 'G' ? '#dbeafe' : '#fed7aa')
                }}
                transition={{ type: 'spring', stiffness: 500 }}
                className={`rounded-lg flex items-center justify-center font-bold text-2xl border-2 ${
                  char === 'G' ? 'border-blue-400' : 'border-orange-400'
                }`}
                style={{
                  width: `${matra * 40}px`,
                  height: '60px'
                }}
              >
                {char}
              </motion.div>
            );
          })}
        </div>

        {/* Mātrā Count Display */}
        <div className="flex flex-wrap gap-2 justify-center mb-6">
          {pattern.matra.map((m, idx) => (
            <div
              key={idx}
              className="text-center"
              style={{ width: `${m * 40}px` }}
            >
              <div className={`text-sm font-medium ${currentBeat === idx ? 'text-purple-700' : 'text-gray-600'}`}>
                {m} mātrā
              </div>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4 justify-center mb-4">
          <Button
            onClick={togglePlay}
            variant={isPlaying ? 'destructive' : 'default'}
            size="lg"
            className="gap-2"
          >
            {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            {isPlaying ? 'Pause' : 'Play'}
          </Button>
          <Button onClick={reset} variant="outline" size="lg" className="gap-2">
            <RotateCcw className="w-5 h-5" />
            Reset
          </Button>
        </div>

        {/* Tempo Control */}
        <div className="max-w-md mx-auto">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Tempo: {tempo} BPM
          </label>
          <input
            type="range"
            min="60"
            max="180"
            value={tempo}
            onChange={(e) => setTempo(parseInt(e.target.value))}
            className="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Legend */}
        <div className="mt-6 grid grid-cols-2 gap-4 max-w-md mx-auto">
          <div className="bg-orange-100 p-3 rounded-lg border-2 border-orange-400">
            <div className="font-bold text-orange-900 text-center">L (Laghu)</div>
            <div className="text-sm text-center text-gray-700">1 mātrā = Short beat</div>
            <div className="text-sm text-center text-gray-600">400 Hz tone</div>
          </div>
          <div className="bg-blue-100 p-3 rounded-lg border-2 border-blue-400">
            <div className="font-bold text-blue-900 text-center">G (Guru)</div>
            <div className="text-sm text-center text-gray-700">2 mātrās = Long beat</div>
            <div className="text-sm text-center text-gray-600">600 Hz tone</div>
          </div>
        </div>
      </div>

      {/* Comparison with Musical Notation */}
      <div className="bg-indigo-50 p-6 rounded-lg border-2 border-indigo-300">
        <h3 className="font-bold text-lg mb-4">Musical Notation Equivalents</h3>
        <div className="space-y-3">
          <div className="bg-white p-4 rounded flex items-center gap-4">
            <span className="font-bold text-orange-600 text-2xl w-12">L</span>
            <span className="text-gray-700">= Eighth note (♪) = <strong>ta</strong> in tabla = <strong>ti</strong> in konnakol</span>
          </div>
          <div className="bg-white p-4 rounded flex items-center gap-4">
            <span className="font-bold text-blue-600 text-2xl w-12">G</span>
            <span className="text-gray-700">= Quarter note (♩) = <strong>taa</strong> in tabla = <strong>tom</strong> in konnakol</span>
          </div>
        </div>
        <p className="mt-4 text-sm text-gray-600 italic">
          The same rhythmic principles that govern Sanskrit prosody are used in Indian classical music!
        </p>
      </div>
    </div>
  );
};

export default RhythmVisualizer;
