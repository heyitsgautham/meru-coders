import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { countPatterns, patternsOfMatras } from './lgPatterns';

interface Pattern {
  pattern: string;
  length: number;
}

const FibonacciVisualizer: React.FC = () => {
  const [selectedLength, setSelectedLength] = useState(3);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [fibSequence, setFibSequence] = useState<number[]>([]);

  useEffect(() => {
    setPatterns(patternsOfMatras(selectedLength).map((pattern) => ({ pattern, length: selectedLength })));
    // Patterns for 1 to 8 mātrās
    setFibSequence(Array.from({ length: 8 }, (_, i) => countPatterns(i + 1)));
  }, [selectedLength]);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border-2 border-green-200">
        <h3 className="font-bold text-lg mb-4">Interactive Pattern Generator</h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select length in mātrās: {selectedLength}
          </label>
          <input
            type="range"
            min="1"
            max="8"
            value={selectedLength}
            onChange={(e) => setSelectedLength(parseInt(e.target.value))}
            className="w-full h-2 bg-green-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="bg-green-50 p-4 rounded">
            <div className="text-sm text-gray-600">Length</div>
            <div className="text-3xl font-bold text-green-700">{selectedLength}</div>
          </div>
          <div className="bg-amber-50 p-4 rounded">
            <div className="text-sm text-gray-600">Number of Patterns</div>
            <div className="text-3xl font-bold text-amber-700">{patterns.length}</div>
          </div>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
          <h4 className="font-semibold mb-3 text-sm text-gray-700">
            All possible L-G patterns ({patterns.length} total):
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {patterns.map((p, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className="bg-white px-3 py-2 rounded border border-gray-200 font-mono text-sm"
              >
                {p.pattern.split('').map((char, i) => (
                  <span
                    key={i}
                    className={char === 'L' ? 'text-orange-600 font-bold' : 'text-blue-600 font-bold'}
                  >
                    {char}
                  </span>
                ))}
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Fibonacci Sequence Visualization */}
      {/* Inline styles: the gradient, wrap and baseline utilities are not in the precompiled index.css. */}
      <div
        className="p-6 rounded-lg border-2"
        style={{ background: 'linear-gradient(to right, #f0fdf4, #ecfdf5)', borderColor: '#86efac' }}
      >
        <h3 className="font-bold text-lg mb-4">Fibonacci Sequence of L-G Combinations</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', justifyContent: 'center', gap: '12px' }}>
          {fibSequence.map((num, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1, type: 'spring' }}
            >
              <div
                data-testid="fib-bar"
                style={{
                  width: '64px',
                  height: `${Math.min(28 + num * 5, 200)}px`,
                  display: 'flex',
                  alignItems: 'flex-end',
                  justifyContent: 'center',
                  paddingBottom: '8px',
                  borderRadius: '8px 8px 0 0',
                  background: 'linear-gradient(to top, #16a34a, #34d399)',
                  color: '#fff',
                  fontSize: '18px',
                  fontWeight: 700,
                }}
              >
                {num}
              </div>
              <div className="text-center mt-2 text-sm font-medium text-gray-700">
                n={idx + 1}
              </div>
            </motion.div>
          ))}
        </div>
        <p className="text-center text-gray-700" style={{ marginTop: '24px' }}>
          Number of L-G patterns: <strong>1, 2, 3, 5, 8, 13, 21, 34...</strong> (Fibonacci!)
        </p>
      </div>
    </div>
  );
};

export default FibonacciVisualizer;
