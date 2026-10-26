import { Brain, Calculator, Heart, Leaf, Music, Wind } from 'lucide-react';

/** Closing card that sums up the six rhythms the page explores. */
export function LabSummary() {
  return (
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
  );
}
