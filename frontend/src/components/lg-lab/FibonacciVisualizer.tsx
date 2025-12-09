import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface Pattern {
  pattern: string;
  length: number;
}

const FibonacciVisualizer: React.FC = () => {
  const [selectedLength, setSelectedLength] = useState(3);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [fibSequence, setFibSequence] = useState<number[]>([]);

  // Generate all possible L-G patterns for a given length
  const generatePatterns = (n: number): Pattern[] => {
    if (n === 0) return [{ pattern: '', length: 0 }];
    if (n === 1) return [{ pattern: 'L', length: 1 }, { pattern: 'G', length: 2 }];
    
    const result: Pattern[] = [];
    const prev1 = generatePatterns(n - 1);
    const prev2 = generatePatterns(n - 2);
    
    // Add L to all patterns of length n-1
    prev1.forEach(p => {
      if (p.length < n) {
        result.push({ pattern: p.pattern + 'L', length: p.length + 1 });
      }
    });
    
    // Add G to all patterns of length n-2
    prev2.forEach(p => {
      if (p.length < n) {
        result.push({ pattern: p.pattern + 'G', length: p.length + 2 });
      }
    });
    
    // Filter patterns that exactly match the target length
    return result.filter(p => p.length === n);
  };

  // Calculate Fibonacci sequence up to n
  const calculateFibonacci = (n: number): number[] => {
    if (n <= 0) return [];
    if (n === 1) return [2];
    
    const fib = [2, 3]; // Start with F(1)=2, F(2)=3 for L-G patterns
    for (let i = 2; i < n; i++) {
      fib.push(fib[i - 1] + fib[i - 2]);
    }
    return fib.slice(0, n);
  };

  useEffect(() => {
    const generated = generatePatterns(selectedLength);
    setPatterns(generated);
    setFibSequence(calculateFibonacci(8));
  }, [selectedLength]);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border-2 border-green-200">
        <h3 className="font-bold text-lg mb-4">Interactive Pattern Generator</h3>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select chandas length (syllables): {selectedLength}
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
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border-2 border-green-300">
        <h3 className="font-bold text-lg mb-4">Fibonacci Sequence of L-G Combinations</h3>
        <div className="flex flex-wrap items-end gap-3 justify-center">
          {fibSequence.map((num, idx) => (
            <motion.div
              key={idx}
              initial={{ height: 0 }}
              animate={{ height: `${Math.min(num * 8, 200)}px` }}
              transition={{ delay: idx * 0.1, type: 'spring' }}
              className="relative"
            >
              <div
                className="w-16 bg-gradient-to-t from-green-600 to-emerald-400 rounded-t-lg flex flex-col items-center justify-end pb-2"
                style={{ height: `${Math.min(num * 8, 200)}px` }}
              >
                <span className="text-white font-bold text-lg">{num}</span>
              </div>
              <div className="text-center mt-2 text-sm font-medium text-gray-700">
                n={idx + 1}
              </div>
            </motion.div>
          ))}
        </div>
        <p className="text-center mt-6 text-gray-700">
          Number of L-G patterns: <strong>2, 3, 5, 8, 13, 21, 34, 55...</strong> (Fibonacci!)
        </p>
      </div>
    </div>
  );
};

export default FibonacciVisualizer;
