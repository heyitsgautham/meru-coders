/** The Cognition tab: why oral tradition favoured regular laghu-guru meters. */
export function CognitionNotes() {
  return (
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
  );
}
