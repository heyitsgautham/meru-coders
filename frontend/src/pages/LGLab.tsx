import React, { useState, Suspense, lazy } from 'react';
import { useNavigate } from 'react-router-dom';
import { Brain, Music, Wind, Leaf, Calculator } from 'lucide-react';
import { CognitionNotes } from '@/components/lg-lab/page/CognitionNotes';
import { LabFooter } from '@/components/lg-lab/page/LabFooter';
import { LabHero } from '@/components/lg-lab/page/LabHero';
import { LabSection, LoadingSpinner } from '@/components/lg-lab/page/LabSection';
import { LabSummary } from '@/components/lg-lab/page/LabSummary';
import '@/styles/lg-lab-utilities.css';

// Lazy load heavy components
const FibonacciVisualizer = lazy(() => import('@/components/lg-lab/FibonacciVisualizer'));
const RhythmVisualizer = lazy(() => import('@/components/lg-lab/RhythmVisualizer'));
const BreathPatternSimulator = lazy(() => import('@/components/lg-lab/BreathPatternSimulator'));
const NaturePatternComparison = lazy(() => import('@/components/lg-lab/NaturePatternComparison'));
const CombinatoricsCalculator = lazy(() => import('@/components/lg-lab/CombinatoricsCalculator'));

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
    <div className="lg-lab-page" style={{ 
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

      <LabHero onBack={() => navigate('/')} />

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

          {activeTab === 'breath' && (
            <LabSection
              icon={<Wind size={32} color="#1976d2" />}
              tint="#e3f2fd"
              title="Human Breath Rhythm"
              subtitle="The biggest real-world link: chandas patterns align with human respiration cycles"
            >
              <Suspense fallback={<LoadingSpinner />}>
                <BreathPatternSimulator />
              </Suspense>
            </LabSection>
          )}

          {activeTab === 'music' && (
            <LabSection
              icon={<Music size={32} color="#7b1fa2" />}
              tint="#f3e5f5"
              title="Music & Time-Keeping (Tāla System)"
              subtitle="Laghu–guru = short beat – long beat, perfectly mapping to musical rhythm"
            >
              <Suspense fallback={<LoadingSpinner />}>
                <RhythmVisualizer />
              </Suspense>
            </LabSection>
          )}

          {activeTab === 'math' && (
            <LabSection
              icon={<Calculator size={32} color="#388e3c" />}
              tint="#e8f5e9"
              title="Mathematics: Pingala & Fibonacci"
              subtitle="The number of L-G pattern combinations follows the Fibonacci sequence!"
            >
              <Suspense fallback={<LoadingSpinner />}>
                <FibonacciVisualizer />
              </Suspense>

              <div style={{ marginTop: '48px' }}>
                <Suspense fallback={<LoadingSpinner />}>
                  <CombinatoricsCalculator />
                </Suspense>
              </div>
            </LabSection>
          )}

          {activeTab === 'nature' && (
            <LabSection
              icon={<Leaf size={32} color="#00897b" />}
              tint="#e0f2f1"
              title="Nature Loves Binary Rhythms"
              subtitle="Laghu–guru (short–long) appears everywhere in the natural world"
            >
              <Suspense fallback={<LoadingSpinner />}>
                <NaturePatternComparison />
              </Suspense>
            </LabSection>
          )}

          {activeTab === 'cognition' && (
            <LabSection
              icon={<Brain size={32} color="#d81b60" />}
              tint="#fce4ec"
              title="Cognition & Memory"
              subtitle="How L-G patterns optimize human memory and consciousness"
            >
              <CognitionNotes />
            </LabSection>
          )}

          <LabSummary />
        </div>
      </section>

      <LabFooter />
    </div>
  );
};

export default LGLab;
