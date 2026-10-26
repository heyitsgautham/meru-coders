import { ArrowLeft } from 'lucide-react';

/** Fixed bar with the way back home, and the page's opening question. */
export function LabHero({ onBack }: { onBack: () => void }) {
  return (
    <>
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
            onClick={onBack}
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
    </>
  );
}
