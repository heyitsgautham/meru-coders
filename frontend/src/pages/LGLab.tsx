import React, { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Brain, Music, Wind, Leaf, Calculator, Heart } from 'lucide-react';

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

  const tabs = [
    { id: 'breath', icon: <Wind size={20} />, label: 'Breath Rhythm', color: '#1976d2' },
    { id: 'music', icon: <Music size={20} />, label: 'Music & Tāla', color: '#7b1fa2' },
    { id: 'math', icon: <Calculator size={20} />, label: 'Mathematics', color: '#388e3c' },
    { id: 'nature', icon: <Leaf size={20} />, label: 'Nature Patterns', color: '#00897b' },
    { id: 'cognition', icon: <Brain size={20} />, label: 'Cognition', color: '#d81b60' }
  ];

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
        .section-card {
          background-color: white;
          border-radius: 16px;
          padding: 48px;
          border: 1px solid #e8e0d5;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
          margin-bottom: 32px;
        }
        @media (max-width: 768px) {
          .section-card {
            padding: 24px;
          }
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
        padding: '0 24px 100px',
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
            {tabs.map((tab) => (
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

          {/* Tab Content: Breath Rhythm */}
          {activeTab === 'breath' && (
            <div className="fade-in section-card">
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

              <Suspense fallback={<LoadingSpinner />}>
                <BreathPatternSimulator />
              </Suspense>
            </div>
          )}

          {/* Tab Content: Music & Tāla */}
          {activeTab === 'music' && (
            <div className="fade-in section-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: '#f3e5f5',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Music size={32} color="#7b1fa2" />
                </div>
                <div>
                  <h2 style={{
                    fontSize: '32px',
                    fontWeight: 700,
                    color: '#1a1a1a',
                    marginBottom: '8px',
                    letterSpacing: '-0.5px'
                  }}>
                    Music & Time-Keeping (Tāla System)
                  </h2>
                  <p style={{ fontSize: '16px', color: '#666' }}>
                    Laghu–guru = short beat – long beat, perfectly mapping to musical rhythm
                  </p>
                </div>
              </div>

              <Suspense fallback={<LoadingSpinner />}>
                <RhythmVisualizer />
              </Suspense>
            </div>
          )}

          {/* Tab Content: Mathematics */}
          {activeTab === 'math' && (
            <div className="fade-in section-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: '#e8f5e9',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Calculator size={32} color="#388e3c" />
                </div>
                <div>
                  <h2 style={{
                    fontSize: '32px',
                    fontWeight: 700,
                    color: '#1a1a1a',
                    marginBottom: '8px',
                    letterSpacing: '-0.5px'
                  }}>
                    Mathematics: Pingala & Fibonacci
                  </h2>
                  <p style={{ fontSize: '16px', color: '#666' }}>
                    The number of L-G pattern combinations follows the Fibonacci sequence!
                  </p>
                </div>
              </div>

              <Suspense fallback={<LoadingSpinner />}>
                <FibonacciVisualizer />
              </Suspense>

              <div style={{ marginTop: '48px' }}>
                <Suspense fallback={<LoadingSpinner />}>
                  <CombinatoricsCalculator />
                </Suspense>
              </div>
            </div>
          )}

          {/* Tab Content: Nature Patterns */}
          {activeTab === 'nature' && (
            <div className="fade-in section-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: '#e0f2f1',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Leaf size={32} color="#00897b" />
                </div>
                <div>
                  <h2 style={{
                    fontSize: '32px',
                    fontWeight: 700,
                    color: '#1a1a1a',
                    marginBottom: '8px',
                    letterSpacing: '-0.5px'
                  }}>
                    Nature Loves Binary Rhythms
                  </h2>
                  <p style={{ fontSize: '16px', color: '#666' }}>
                    Laghu–guru (short–long) appears everywhere in the natural world
                  </p>
                </div>
              </div>

              <Suspense fallback={<LoadingSpinner />}>
                <NaturePatternComparison />
              </Suspense>
            </div>
          )}

          {/* Tab Content: Cognition */}
          {activeTab === 'cognition' && (
            <div className="fade-in section-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
                <div style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '16px',
                  backgroundColor: '#fce4ec',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Brain size={32} color="#d81b60" />
                </div>
                <div>
                  <h2 style={{
                    fontSize: '32px',
                    fontWeight: 700,
                    color: '#1a1a1a',
                    marginBottom: '8px',
                    letterSpacing: '-0.5px'
                  }}>
                    Cognition & Memory
                  </h2>
                  <p style={{ fontSize: '16px', color: '#666' }}>
                    How L-G patterns optimize human memory and consciousness
                  </p>
                </div>
              </div>

              <div style={{ fontSize: '18px', color: '#555', lineHeight: 1.8 }}>
                <p style={{ marginBottom: '24px' }}>
                  Brain studies show that repeating binary rhythmic patterns are the easiest to memorize. 
                  Regular short-long patterns increase <strong>mnemonic efficiency</strong> and create 
                  <strong>brainwave entrainment</strong> when chanting in fixed meters.
                </p>

                <div style={{
                  backgroundColor: '#fce4ec',
                  padding: '32px',
                  borderRadius: '12px',
                  marginBottom: '32px'
                }}>
                  <h3 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '20px', color: '#1a1a1a' }}>
                    Oral Tradition Requirements
                  </h3>
                  <p style={{ color: '#555', marginBottom: '16px' }}>
                    The Vedic traditions were <strong>purely oral</strong>, so meter needed to be:
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <span style={{ color: '#d81b60', fontWeight: 700 }}>✔️</span>
                      <span style={{ color: '#555' }}>Easy to remember</span>
                    </div>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <span style={{ color: '#d81b60', fontWeight: 700 }}>✔️</span>
                      <span style={{ color: '#555' }}>Easy to recite</span>
                    </div>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <span style={{ color: '#d81b60', fontWeight: 700 }}>✔️</span>
                      <span style={{ color: '#555' }}>Resistant to corruption over generations</span>
                    </div>
                  </div>
                </div>

                <div style={{
                  backgroundColor: '#fff8f0',
                  padding: '32px',
                  borderRadius: '12px',
                  border: '1px solid #ffe0b2'
                }}>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px', color: '#e65100' }}>
                    Consciousness & Meter
                  </h3>
                  <p style={{ color: '#555', marginBottom: '12px' }}>
                    Advanced practitioners report that prolonged chanting in classical meters induces:
                  </p>
                  <ul style={{ color: '#555', paddingLeft: '20px', margin: 0 }}>
                    <li>Alpha-theta brainwave states (meditation)</li>
                    <li>Enhanced phonological awareness</li>
                    <li>Improved linguistic memory formation</li>
                    <li>Synchronized left-right hemisphere activity</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Final Summary */}
          <div className="fade-in" style={{
            backgroundColor: 'white',
            borderRadius: '16px',
            padding: '48px',
            border: '4px solid #c75b1a',
            marginTop: '60px',
            textAlign: 'center'
          }}>
            <h2 style={{
              fontSize: '36px',
              fontWeight: 700,
              color: '#4a2c10',
              marginBottom: '32px',
              letterSpacing: '-0.5px'
            }}>
              🔥 Final Answer
            </h2>
            
            <p style={{
              fontSize: '24px',
              fontWeight: 700,
              color: '#1a1a1a',
              marginBottom: '32px',
              lineHeight: 1.4
            }}>
              YES — laghu–guru patterns form exact, mathematical sequences because they reflect:
            </p>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              marginBottom: '32px'
            }}>
              {[
                { icon: <Wind size={32} />, label: 'Human Breathing', color: '#1976d2' },
                { icon: <Music size={32} />, label: 'Musical Timing', color: '#7b1fa2' },
                { icon: <Brain size={32} />, label: 'Brain Rhythms', color: '#d81b60' },
                { icon: <Leaf size={32} />, label: 'Natural Oscillations', color: '#00897b' },
                { icon: <Calculator size={32} />, label: 'Fibonacci Math', color: '#388e3c' },
                { icon: <Heart size={32} />, label: 'Universal Rhythms', color: '#c62828' }
              ].map((item, i) => (
                <div key={i} style={{
                  backgroundColor: '#faf7f2',
                  padding: '24px',
                  borderRadius: '12px',
                  border: '1px solid #e8e0d5'
                }}>
                  <div style={{ color: item.color, marginBottom: '12px' }}>
                    {item.icon}
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '14px', color: '#1a1a1a' }}>
                    {item.label}
                  </div>
                </div>
              ))}
            </div>

            <div style={{
              backgroundColor: '#fff8f0',
              padding: '32px',
              borderRadius: '12px',
              border: '2px solid #ffe0b2'
            }}>
              <p style={{
                fontSize: '20px',
                color: '#555',
                lineHeight: 1.7,
                marginBottom: '16px'
              }}>
                They're not arbitrary — they are <strong style={{ color: '#c75b1a' }}>nature expressed through sound</strong>.
              </p>
              <p style={{
                fontSize: '24px',
                fontWeight: 700,
                color: '#c75b1a',
                margin: 0
              }}>
                Classical chandas are <em>the mathematics of breath</em> and <em>the music of consciousness</em>.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '40px 24px',
        backgroundColor: '#4a2c10',
        color: 'white',
        textAlign: 'center'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto'
        }}>
          <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>
            Meru Coders
          </div>
          <div style={{ fontSize: '14px', color: 'rgba(255, 255, 255, 0.7)' }}>
            Sanskrit Meter Identification Tool - L-G Laboratory
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LGLab;
