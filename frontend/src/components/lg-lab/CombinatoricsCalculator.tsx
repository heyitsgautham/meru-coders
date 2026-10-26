import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calculator, Sparkles } from 'lucide-react';
import { countPatterns, patternsOfMatras } from './lgPatterns';

interface PatternCount {
  length: number;
  count: number;
  patterns: string[];
}

const CombinatoricsCalculator: React.FC = () => {
  const [inputLength, setInputLength] = useState(5);
  const [showAllPatterns, setShowAllPatterns] = useState(false);
  const [patternData, setPatternData] = useState<PatternCount | null>(null);
  const [fibSequence, setFibSequence] = useState<number[]>([]);

  useEffect(() => {
    const patterns = patternsOfMatras(inputLength);
    const count = patterns.length;
    
    setPatternData({
      length: inputLength,
      count: count,
      patterns: patterns
    });

    // Generate Fibonacci sequence for comparison
    const fib: number[] = [];
    for (let i = 0; i <= 10; i++) {
      fib.push(countPatterns(i));
    }
    setFibSequence(fib);
  }, [inputLength]);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border-2 border-green-300">
        <div className="flex items-center gap-3 mb-4">
          <Calculator className="w-8 h-8 text-green-600" />
          <h3 className="font-bold text-xl">Combinatorics Calculator</h3>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enter mātrā length (1-10): <span className="text-2xl font-bold text-green-700">{inputLength}</span>
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={inputLength}
            onChange={(e) => setInputLength(parseInt(e.target.value))}
            className="w-full h-3 bg-green-200 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {patternData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {/* Result Display */}
            <div className="grid md:grid-cols-3 gap-4">
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600 mb-1">Mātrā Length</div>
                <div className="text-3xl font-bold text-green-700">{patternData.length}</div>
              </div>
              <div className="bg-amber-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600 mb-1">Total Combinations</div>
                <div className="text-3xl font-bold text-amber-700">{patternData.count}</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-600 mb-1">Fibonacci F({patternData.length})</div>
                <div className="text-3xl font-bold text-blue-700">
                  {fibSequence[patternData.length]}
                </div>
              </div>
            </div>

            {/* Fibonacci Verification */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border-2 border-green-300">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-green-900">Fibonacci Verification</span>
              </div>
              <p className="text-gray-700 text-sm">
                {patternData.count === fibSequence[patternData.length] ? (
                  <span className="text-green-700 font-semibold">
                    ✓ Confirmed! The count matches Fibonacci number F({patternData.length}) = {fibSequence[patternData.length]}
                  </span>
                ) : (
                  <span className="text-amber-700">
                    Note: For mātrā-based counting, the sequence may differ slightly from standard Fibonacci.
                  </span>
                )}
              </p>
            </div>

            {/* Pattern List Toggle */}
            <div className="text-center">
              <button
                onClick={() => setShowAllPatterns(!showAllPatterns)}
                className="px-6 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors"
              >
                {showAllPatterns ? 'Hide' : 'Show'} All {patternData.count} Patterns
              </button>
            </div>

            {/* Pattern Grid */}
            {showAllPatterns && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto"
              >
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                  {patternData.patterns.map((pattern, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.02 }}
                      className="bg-white p-2 rounded border border-gray-200 font-mono text-center"
                    >
                      {pattern.split('').map((char, i) => (
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
              </motion.div>
            )}
          </motion.div>
        )}
      </div>

      {/* Fibonacci Table */}
      <div className="bg-white p-6 rounded-lg border-2 border-blue-300">
        <h4 className="font-bold text-lg mb-4">Complete Fibonacci Table (mātrā length → combinations)</h4>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-blue-50">
                <th className="px-4 py-2 text-left font-semibold">Mātrā Length (n)</th>
                {fibSequence.map((_, idx) => (
                  <th key={idx} className="px-3 py-2 text-center font-semibold">{idx}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-t">
                <td className="px-4 py-2 font-semibold bg-blue-50">Combinations F(n)</td>
                {fibSequence.map((num, idx) => (
                  <td
                    key={idx}
                    className={`px-3 py-2 text-center font-mono font-bold ${
                      idx === inputLength ? 'bg-green-200 text-green-900' : ''
                    }`}
                  >
                    {num}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-gray-600 mt-3 italic">
          Green highlight shows the current selected length ({inputLength} mātrās)
        </p>
      </div>

      {/* Mathematical Formula */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-lg border-2 border-purple-300">
        <h4 className="font-bold text-lg mb-3 text-purple-900">The Mathematical Formula</h4>
        <div className="bg-white p-4 rounded-lg mb-3">
          <div className="text-center font-mono text-lg mb-2">
            <strong>F(n) = F(n-1) + F(n-2)</strong>
          </div>
          <div className="text-center text-sm text-gray-600">
            with F(0) = 1, F(1) = 1
          </div>
        </div>
        <div className="space-y-2 text-gray-700 text-sm">
          <p>
            <strong>F(n-1):</strong> All patterns of length (n-1) can be extended by adding <span className="text-orange-600 font-bold">L</span> (1 mātrā)
          </p>
          <p>
            <strong>F(n-2):</strong> All patterns of length (n-2) can be extended by adding <span className="text-blue-600 font-bold">G</span> (2 mātrās)
          </p>
          <p className="pt-2 border-t">
            This is the <strong>exact same recurrence relation</strong> that generates the Fibonacci sequence, 
            discovered by Pingala in his Chandas Shastra (500-200 BCE) — over 1,500 years before Fibonacci!
          </p>
        </div>
      </div>

      {/* Example Calculation */}
      <div className="bg-amber-50 p-6 rounded-lg border-2 border-amber-300">
        <h4 className="font-bold text-lg mb-3 text-amber-900">Example: Calculating F(4)</h4>
        <div className="space-y-3">
          <div className="bg-white p-4 rounded">
            <div className="font-semibold mb-2">Patterns of length 4 mātrās:</div>
            <div className="grid grid-cols-3 gap-2 font-mono text-sm">
              <div className="bg-green-50 p-2 rounded">LLLL</div>
              <div className="bg-green-50 p-2 rounded">LLG</div>
              <div className="bg-green-50 p-2 rounded">LGL</div>
              <div className="bg-green-50 p-2 rounded">GLL</div>
              <div className="bg-green-50 p-2 rounded">GG</div>
            </div>
            <div className="mt-2 font-semibold text-green-700">Total: 5 patterns</div>
          </div>
          <div className="bg-white p-4 rounded">
            <div className="font-semibold mb-2">Verification:</div>
            <div className="font-mono">
              F(4) = F(3) + F(2) = 3 + 2 = <span className="text-green-700 font-bold">5</span> ✓
            </div>
          </div>
        </div>
      </div>

      {/* Applications */}
      <div className="bg-blue-50 p-6 rounded-lg border-2 border-blue-300">
        <h4 className="font-bold text-lg mb-3 text-blue-900">Why This Matters</h4>
        <ul className="space-y-2 text-gray-700">
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Ancient Computer Science:</strong> Pingala discovered recursive algorithms and combinatorics 
              millennia before modern mathematics
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Meter Database:</strong> Knowing the total combinations helps validate chandas databases 
              for completeness
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Pattern Generation:</strong> This formula enables systematic generation of all possible 
              meters for any syllable length
            </span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">•</span>
            <span>
              <strong>Universal Mathematics:</strong> The same pattern appears in nature (phyllotaxis), 
              music, architecture, and genetics
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default CombinatoricsCalculator;
