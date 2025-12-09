import React, { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Brain, Music, Wind, Leaf, Calculator, Heart, Waves, Bird, Sparkles } from 'lucide-react';

// Lazy load heavy components
const FibonacciVisualizer = lazy(() => import('@/components/lg-lab/FibonacciVisualizer'));
const RhythmVisualizer = lazy(() => import('@/components/lg-lab/RhythmVisualizer'));
const BreathPatternSimulator = lazy(() => import('@/components/lg-lab/BreathPatternSimulator'));
const NaturePatternComparison = lazy(() => import('@/components/lg-lab/NaturePatternComparison'));
const CombinatoricsCalculator = lazy(() => import('@/components/lg-lab/CombinatoricsCalculator'));

const LoadingSpinner = () => (
  <div style={{ 
    display: 'flex', 
    alignItems: 'center', 
    justifyContent: 'center', 
    padding: '60px 24px' 
  }}>
    <div style={{
      width: '48px',
      height: '48px',
      borderRadius: '50%',
      border: '3px solid #e8e0d5',
      borderTopColor: '#c75b1a',
      animation: 'spin 1s linear infinite'
    }} />
  </div>
);

const LGLab: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('breath');

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#faf7f2',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    }}>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
          animation: fadeIn 0.6s ease-out;
        }
      `}</style>

      {/* Navigation Bar */}
      <nav style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        height: '70px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #e8e0d5',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <button
            onClick={() => navigate('/')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '8px 16px',
              backgroundColor: 'transparent',
              color: '#4a2c10',
              border: '1px solid #e8e0d5',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#fff3e6';
              e.currentTarget.style.borderColor = '#c75b1a';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.borderColor = '#e8e0d5';
            }}
          >
            <ArrowLeft size={16} />
            Back to Home
          </button>
          
          <span style={{ 
            fontSize: '20px', 
            fontWeight: 700, 
            color: '#4a2c10',
            letterSpacing: '-0.5px'
          }}>
            L-G Laboratory
          </span>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        paddingTop: '120px',
        paddingBottom: '60px',
        paddingLeft: '24px',
        paddingRight: '24px',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div className="fade-in" style={{
          width: '100%',
          maxWidth: '1200px',
          textAlign: 'center'
        }}>
          <div style={{
            display: 'inline-block',
            padding: '6px 14px',
            backgroundColor: '#fff3e6',
            borderRadius: '20px',
            marginBottom: '20px'
          }}>
            <span style={{ 
              fontSize: '12px', 
              fontWeight: 600, 
              color: '#c75b1a',
              letterSpacing: '0.5px'
            }}>
              INTERACTIVE EXPLORATION
            </span>
          </div>

          <h1 style={{
            fontSize: '48px',
            fontWeight: 700,
            color: '#1a1a1a',
            lineHeight: 1.15,
            marginBottom: '24px',
            letterSpacing: '-1.5px'
          }}>
            🔬 L-G Laboratory
          </h1>
          
          <p style={{
            fontSize: '20px',
            color: '#5a5a5a',
            lineHeight: 1.7,
            marginBottom: '32px',
            maxWidth: '800px',
            margin: '0 auto 48px'
          }}>
            Explore the deep connections between Laghu-Guru patterns and the rhythms of nature, 
            mathematics, music, and human consciousness
          </p>

          {/* Hero Insight Card */}
          <div style={{
            backgroundColor: '#fff8f0',
            borderLeft: '4px solid #c75b1a',
            padding: '32px 40px',
            marginBottom: '60px',
            borderRadius: '0 16px 16px 0',
            maxWidth: '900px',
            margin: '0 auto 60px',
            textAlign: 'left'
          }}>
            <div style={{ display: 'flex', alignItems: 'start', gap: '20px' }}>
              <div style={{ fontSize: '48px', flexShrink: 0 }}>🌺</div>
              <div>
                <h2 style={{
                  fontSize: '24px',
                  fontWeight: 700,
                  color: '#4a2c10',
                  marginBottom: '16px',
                  lineHeight: 1.3
                }}>
                  Why do classical chandas have such exact Laghu–Guru patterns?
                </h2>
                <p style={{
                  fontSize: '18px',
                  color: '#555',
                  lineHeight: 1.7,
                  marginBottom: '20px'
                }}>
                  Because humans, nature, and language itself follow <strong>predictable rhythmic laws</strong>! 
                  Those ancient chanda-śāstrīs weren't just making patterns — they were <em>discovering</em> the 
                  patterns already embedded in the world.
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                  {['Human Breath Rhythm', 'Musical Time-Keeping', 'Fibonacci Mathematics', 'Natural Binary Rhythms', 'Cognitive Entrainment'].map((tag, i) => (
                    <span key={i} style={{
                      padding: '8px 16px',
                      backgroundColor: 'white',
                      borderRadius: '20px',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#c75b1a',
                      border: '1px solid #e8e0d5'
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Interactive Tabs */}
      <section style={{
        padding: '0 24px 80px',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <div style={{
          width: '100%',
          maxWidth: '1200px'
        }}>
          {/* Tab Navigation */}
          <div style={{
            display: 'flex',
            gap: '12px',
            marginBottom: '48px',
            overflowX: 'auto',
            padding: '8px',
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e8e0d5',
            boxShadow: '0 2px 12px rgba(0, 0, 0, 0.04)'
          }}>
            {[
              { id: 'breath', icon: <Wind size={20} />, label: 'Breath Rhythm' },
              { id: 'music', icon: <Music size={20} />, label: 'Music & Tāla' },
              { id: 'math', icon: <Calculator size={20} />, label: 'Mathematics' },
              { id: 'nature', icon: <Leaf size={20} />, label: 'Nature Patterns' },
              { id: 'cognition', icon: <Brain size={20} />, label: 'Cognition' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  flex: 1,
                  minWidth: '140px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '16px 20px',
                  backgroundColor: activeTab === tab.id ? '#c75b1a' : 'transparent',
                  color: activeTab === tab.id ? 'white' : '#666',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.backgroundColor = '#f8f9fa';
                  }
                }}
                onMouseOut={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }
                }}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === 'breath' && (
            <div className="fade-in" style={{
              backgroundColor: 'white',
              borderRadius: '16px',
              padding: '48px',
              border: '1px solid #e8e0d5',
              boxShadow: '0 4px 24px rgba(0, 0, 0, 0.06)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: '#e3f2fd',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Wind size={32} color="#1976d2" />
                </div>
                <div>
                  <h2 style={{
                    fontSize: '32px',
                    fontWeight: 700,
                    color: '#1a1a1a',
                    marginBottom: '8px',
                    letterSpacing: '-0.5px'
                  }}>
                    Human Breath Rhythm
                  </h2>
                  <p style={{ fontSize: '16px', color: '#666' }}>
                    The biggest real-world link: chandas patterns align with human respiration cycles
                  </p>
                </div>
              </div>

              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '32px',
                marginBottom: '48px'
              }}>
                <div style={{
                  backgroundColor: '#e3f2fd',
                  padding: '32px',
                  borderRadius: '12px'
                }}>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px', color: '#1a1a1a' }}>
                    The Connection
                  </h3>
                  <div style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'start', gap: '12px', marginBottom: '12px' }}>
                      <span style={{ fontSize: '20px', fontWeight: 700, color: '#1976d2' }}>G</span>
                      <span style={{ color: '#555', lineHeight: 1.6 }}>
                        Guru syllable ≈ <strong>long breath unit</strong>
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'start', gap: '12px' }}>
                      <span style={{ fontSize: '20px', fontWeight: 700, color: '#f57c00' }}>L</span>
                      <span style={{ color: '#555', lineHeight: 1.6 }}>
                        Laghu syllable ≈ <strong>short breath unit</strong>
                      </span>
                    </div>
                  </div>
                  <p style={{ color: '#555', fontSize: '15px', lineHeight: 1.7 }}>
                    Ancient poets composed for oral recitation, so the meter had to match 
                    how long a human can speak without breaking breath.
                  </p>
                </div>

                <div style={{
                  backgroundColor: '#e8f5e9',
                  padding: '32px',
                  borderRadius: '12px'
                }}>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px', color: '#1a1a1a' }}>
                    Classical Examples
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div>
                      <div style={{ fontWeight: 600, color: '#2e7d32', fontSize: '16px' }}>Gāyatrī</div>
                      <div style={{ fontSize: '14px', color: '#666', marginTop: '4px' }}>
                        8 syllables/pāda → fits one natural breath
                      </div>
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#2e7d32', fontSize: '16px' }}>Anuṣṭubh</div>
                      <div style={{ fontSize: '14px', color: '#666', marginTop: '4px' }}>
                        8+8+8+8 → comfortable two-breath pattern
                      </div>
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#2e7d32', fontSize: '16px' }}>Triṣṭubh</div>
                      <div style={{ fontSize: '14px', color: '#666', marginTop: '4px' }}>
                        11 syllables/pāda → extended breath for advanced chanters
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <Suspense fallback={<LoadingSpinner />}>
                <BreathPatternSimulator />
              </Suspense>

              <div style={{
                marginTop: '48px',
                padding: '24px',
                backgroundColor: '#fff8f0',
                borderRadius: '12px',
                border: '1px solid #ffe0b2'
              }}>
                <p style={{ fontSize: '15px', fontWeight: 600, color: '#f57c00', margin: 0 }}>
                  ✔️ Respiration cycles • ✔️ Speech energy • ✔️ Breath control of priests during chanting
                </p>
                <p style={{ color: '#e65100', marginTop: '8px', fontWeight: 600, fontSize: '16px' }}>
                  Real world → Human Biology!
                </p>
              </div>
            </div>
          )}

          {/* 2. Music & Tāla Tab */}
          <TabsContent value="music">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Music className="w-8 h-8 text-purple-600" />
                    Music & Time-Keeping (Tāla System Connection)
                  </CardTitle>
                  <CardDescription className="text-base">
                    Laghu–guru = short beat – long beat, perfectly mapping to musical rhythm
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <div className="bg-purple-50 p-6 rounded-lg">
                      <h3 className="font-bold text-lg mb-3">Mātrā Mapping</h3>
                      <div className="space-y-4">
                        <div className="flex items-center gap-4">
                          <div className="w-20 h-12 bg-orange-400 rounded flex items-center justify-center text-white font-bold">
                            L
                          </div>
                          <span className="text-lg">= 1 mātrā</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="w-40 h-12 bg-blue-500 rounded flex items-center justify-center text-white font-bold">
                            G
                          </div>
                          <span className="text-lg">= 2 mātrās</span>
                        </div>
                      </div>
                      <p className="mt-4 text-gray-700">
                        That's exactly how rhythm cycles (tālas) work in Indian classical music!
                      </p>
                    </div>
                    <div className="bg-indigo-50 p-6 rounded-lg">
                      <h3 className="font-bold text-lg mb-3">Ancient Beat Sequences</h3>
                      <p className="text-gray-700 mb-3">Chandas are basically ancient beat sequences, just like:</p>
                      <ul className="space-y-2">
                        <li className="flex items-center gap-2">
                          <span className="text-2xl">•–</span>
                          <span><strong>Morse code:</strong> short + long</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="font-mono">ta taa</span>
                          <span><strong>Drumming:</strong> basic tabla units</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="font-mono">ti tum</span>
                          <span><strong>Konnakol:</strong> South Indian vocal percussion</span>
                        </li>
                      </ul>
                      <p className="mt-4 text-indigo-800 font-semibold">
                        The Vedic priests were the earliest rhythm scientists!
                      </p>
                    </div>
                  </div>
                  
                  <Suspense fallback={<LoadingSpinner />}>
                    <RhythmVisualizer />
                  </Suspense>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* 3. Mathematics Tab */}
          <TabsContent value="math">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Calculator className="w-8 h-8 text-green-600" />
                    Mathematics: Pingala & Fibonacci Sequence
                  </CardTitle>
                  <CardDescription className="text-base">
                    The number of L-G pattern combinations follows the Fibonacci sequence!
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-green-50 p-6 rounded-lg mb-6">
                    <h3 className="font-bold text-xl mb-4">Pingala's Discoveries</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <ul className="space-y-2">
                        <li className="flex items-start gap-2">
                          <span className="text-green-600">✓</span>
                          <span><strong>Binary notation</strong> (before computers!)</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-green-600">✓</span>
                          <span><strong>Recursive pattern generation</strong></span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-green-600">✓</span>
                          <span><strong>Fibonacci sequence</strong></span>
                        </li>
                      </ul>
                      <ul className="space-y-2">
                        <li className="flex items-start gap-2">
                          <span className="text-green-600">✓</span>
                          <span><strong>Combinatorics</strong> on L-G patterns</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-green-600">✓</span>
                          <span><strong>Mount Meru triangle</strong> (Pascal's triangle)</span>
                        </li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-amber-50 p-6 rounded-lg mb-6">
                    <h3 className="font-bold text-lg mb-3">The Fibonacci Connection</h3>
                    <p className="text-gray-700 mb-4">
                      The number of ways to arrange laghu-guru patterns of length n follows the Fibonacci sequence:
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
                      <div className="bg-white p-3 rounded text-center">
                        <div className="text-xs text-gray-600">Length 1</div>
                        <div className="text-2xl font-bold text-green-700">2</div>
                      </div>
                      <div className="bg-white p-3 rounded text-center">
                        <div className="text-xs text-gray-600">Length 2</div>
                        <div className="text-2xl font-bold text-green-700">3</div>
                      </div>
                      <div className="bg-white p-3 rounded text-center">
                        <div className="text-xs text-gray-600">Length 3</div>
                        <div className="text-2xl font-bold text-green-700">5</div>
                      </div>
                      <div className="bg-white p-3 rounded text-center">
                        <div className="text-xs text-gray-600">Length 4</div>
                        <div className="text-2xl font-bold text-green-700">8</div>
                      </div>
                      <div className="bg-white p-3 rounded text-center">
                        <div className="text-xs text-gray-600">Length 5</div>
                        <div className="text-2xl font-bold text-green-700">13</div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 italic">
                      Exact Fibonacci explosion! These patterns align with combinatorics, natural growth patterns, 
                      and recursive math found in plants, shells, and galaxies.
                    </p>
                  </div>

                  <Suspense fallback={<LoadingSpinner />}>
                    <FibonacciVisualizer />
                  </Suspense>

                  <div className="mt-6">
                    <Suspense fallback={<LoadingSpinner />}>
                      <CombinatoricsCalculator />
                    </Suspense>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* 4. Nature Patterns Tab */}
          <TabsContent value="nature">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Leaf className="w-8 h-8 text-emerald-600" />
                    Nature Loves Binary Rhythms
                  </CardTitle>
                  <CardDescription className="text-base">
                    Laghu–guru (short–long) appears everywhere in the natural world
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <div className="space-y-4">
                      <div className="bg-emerald-50 p-4 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <Bird className="w-6 h-6 text-emerald-600" />
                          <h4 className="font-semibold">Bird Songs</h4>
                        </div>
                        <p className="text-sm text-gray-700">
                          Short chirps + long trills = natural L-G patterns
                        </p>
                      </div>
                      
                      <div className="bg-red-50 p-4 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <Heart className="w-6 h-6 text-red-600" />
                          <h4 className="font-semibold">Heartbeats</h4>
                        </div>
                        <p className="text-sm text-gray-700">
                          Lub-dub = classic binary rhythm pattern
                        </p>
                      </div>

                      <div className="bg-blue-50 p-4 rounded-lg">
                        <div className="flex items-center gap-3 mb-2">
                          <Waves className="w-6 h-6 text-blue-600" />
                          <h4 className="font-semibold">Wave Patterns</h4>
                        </div>
                        <p className="text-sm text-gray-700">
                          Ocean waves follow short-long oscillations
                        </p>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="bg-purple-50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">Walking Patterns</h4>
                        <p className="text-sm text-gray-700">
                          Natural gait = short-long stride alternation
                        </p>
                      </div>
                      
                      <div className="bg-cyan-50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">Rainfall Rhythms</h4>
                        <p className="text-sm text-gray-700">
                          Raindrops create natural L-G percussion
                        </p>
                      </div>

                      <div className="bg-amber-50 p-4 rounded-lg">
                        <h4 className="font-semibold mb-2">Neuronal Firing</h4>
                        <p className="text-sm text-gray-700">
                          Brain cells fire in binary rhythmic patterns
                        </p>
                      </div>
                    </div>
                  </div>

                  <Suspense fallback={<LoadingSpinner />}>
                    <NaturePatternComparison />
                  </Suspense>

                  <div className="mt-6 p-6 bg-gradient-to-r from-emerald-50 to-green-50 rounded-lg border-2 border-emerald-300">
                    <p className="text-lg text-gray-800 mb-2">
                      We humans subconsciously <strong>prefer</strong> patterns that resemble these natural oscillations.
                    </p>
                    <p className="text-emerald-900 font-semibold text-xl">
                      That's exactly why chandas feel satisfying — they resonate with nature's fractal rhythms.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>

          {/* 5. Cognition Tab */}
          <TabsContent value="cognition">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-3">
                    <Brain className="w-8 h-8 text-pink-600" />
                    Cognition & Memory
                  </CardTitle>
                  <CardDescription className="text-base">
                    How L-G patterns optimize human memory and consciousness
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-pink-50 p-6 rounded-lg mb-6">
                    <h3 className="font-bold text-xl mb-4">Brain Science Reveals</h3>
                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🧠</span>
                        <div>
                          <h4 className="font-semibold">Mnemonic Efficiency</h4>
                          <p className="text-gray-700">
                            Repeating binary rhythmic patterns are the easiest to memorize
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">⚡</span>
                        <div>
                          <h4 className="font-semibold">Pattern Recognition</h4>
                          <p className="text-gray-700">
                            Regular short-long patterns increase memory retention by 40-60%
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">🎵</span>
                        <div>
                          <h4 className="font-semibold">Brainwave Entrainment</h4>
                          <p className="text-gray-700">
                            Chanting in fixed meters creates synchronization of neural oscillations
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mb-6">
                    <div className="bg-blue-50 p-6 rounded-lg">
                      <h3 className="font-bold text-lg mb-3">Oral Tradition Requirements</h3>
                      <p className="text-gray-700 mb-3">
                        The Vedic traditions were <strong>purely oral</strong>, so meter needed to be:
                      </p>
                      <ul className="space-y-2">
                        <li className="flex items-center gap-2">
                          <span className="text-blue-600">✔️</span>
                          <span>Easy to remember</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="text-blue-600">✔️</span>
                          <span>Easy to recite</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="text-blue-600">✔️</span>
                          <span>Resistant to corruption over generations</span>
                        </li>
                      </ul>
                    </div>

                    <div className="bg-purple-50 p-6 rounded-lg">
                      <h3 className="font-bold text-lg mb-3">Cognitive Stabilizers</h3>
                      <p className="text-gray-700 mb-3">
                        Structured laghu–guru sequences evolved as:
                      </p>
                      <ul className="space-y-2">
                        <li className="flex items-start gap-2">
                          <span className="text-purple-600">→</span>
                          <span><strong>Error-detection mechanisms</strong> (broken meter = corrupted text)</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-purple-600">→</span>
                          <span><strong>Attention anchors</strong> for focused recitation</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-purple-600">→</span>
                          <span><strong>Meditative tools</strong> for consciousness expansion</span>
                        </li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-purple-100 to-pink-100 p-6 rounded-lg border-2 border-purple-300">
                    <h3 className="font-bold text-xl mb-3 text-purple-900">The Memory Experiment</h3>
                    <p className="text-gray-800 mb-4">
                      Try memorizing these two sequences:
                    </p>
                    <div className="space-y-4">
                      <div className="bg-white p-4 rounded">
                        <div className="text-sm text-gray-600 mb-1">Random syllables:</div>
                        <div className="font-mono text-lg">pa ki tu ma jo re si la nu</div>
                      </div>
                      <div className="bg-white p-4 rounded">
                        <div className="text-sm text-gray-600 mb-1">Same syllables in L-G pattern (Anuṣṭubh):</div>
                        <div className="font-mono text-lg">pa ki tu ma | jo re si la</div>
                        <div className="text-xs text-gray-500 mt-1">L L G L | L L G L</div>
                      </div>
                    </div>
                    <p className="text-purple-900 font-semibold mt-4">
                      The second is 3x easier to remember because it has rhythmic structure!
                    </p>
                  </div>

                  <div className="mt-6 p-6 bg-amber-50 rounded-lg">
                    <h3 className="font-bold text-lg mb-2">Consciousness & Meter</h3>
                    <p className="text-gray-700">
                      Advanced practitioners report that prolonged chanting in classical meters induces:
                    </p>
                    <ul className="mt-3 space-y-1 text-gray-800">
                      <li>• Alpha-theta brainwave states (meditation)</li>
                      <li>• Enhanced phonological awareness</li>
                      <li>• Improved linguistic memory formation</li>
                      <li>• Synchronized left-right hemisphere activity</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </TabsContent>
        </Tabs>

        {/* Final Summary Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-8"
        >
          <Card className="bg-gradient-to-br from-orange-100 via-amber-100 to-yellow-100 border-4 border-orange-400">
            <CardHeader>
              <CardTitle className="text-3xl text-center">
                🔥 Final Answer (Powerful Summary)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-900 mb-4">
                  YES — laghu–guru patterns form exact, mathematical sequences because they reflect:
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-lg text-center">
                  <Wind className="w-12 h-12 mx-auto mb-2 text-blue-600" />
                  <h4 className="font-semibold">Human Breathing</h4>
                </div>
                <div className="bg-white p-4 rounded-lg text-center">
                  <Music className="w-12 h-12 mx-auto mb-2 text-purple-600" />
                  <h4 className="font-semibold">Musical Timing</h4>
                </div>
                <div className="bg-white p-4 rounded-lg text-center">
                  <Brain className="w-12 h-12 mx-auto mb-2 text-pink-600" />
                  <h4 className="font-semibold">Brain Rhythm Perception</h4>
                </div>
                <div className="bg-white p-4 rounded-lg text-center">
                  <Leaf className="w-12 h-12 mx-auto mb-2 text-emerald-600" />
                  <h4 className="font-semibold">Natural Binary Oscillations</h4>
                </div>
                <div className="bg-white p-4 rounded-lg text-center">
                  <Calculator className="w-12 h-12 mx-auto mb-2 text-green-600" />
                  <h4 className="font-semibold">Fibonacci Mathematics</h4>
                </div>
                <div className="bg-white p-4 rounded-lg text-center">
                  <Heart className="w-12 h-12 mx-auto mb-2 text-red-600" />
                  <h4 className="font-semibold">Universal Rhythms</h4>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg border-2 border-orange-300">
                <p className="text-xl text-center text-gray-800 leading-relaxed">
                  They're not arbitrary — they are <strong className="text-orange-700">nature expressed through sound</strong>.
                </p>
                <p className="text-2xl text-center font-bold text-orange-900 mt-4">
                  Classical chandas are <em>the mathematics of breath</em> and <em>the music of consciousness</em>.
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default LGLab;
