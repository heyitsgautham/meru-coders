export function Footer() {
  return (
    <footer style={{ width: '100%', marginTop: '40px', paddingBottom: '40px' }}>
      <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Decorative line */}
        <div style={{ width: '160px', height: '1px', background: 'linear-gradient(to right, #fdf8f3, #ff9933, #fdf8f3)', marginBottom: '40px' }} />
        
        <p style={{ color: '#4a2c10', fontSize: '0.875rem', fontWeight: '500', marginBottom: '12px', textAlign: 'center', width: '100%' }}>
          Sanskrit Meter Identification System
        </p>
        <p style={{ color: '#9a6a3a', fontSize: '0.875rem', marginBottom: '24px', textAlign: 'center', width: '100%' }}>
          Advanced meter analysis for Sanskrit texts
        </p>
        
        {/* Decorative dots */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#ff9933' }} />
          <div style={{ color: '#ff9933', fontSize: '1.125rem', fontWeight: 'bold' }}>॥</div>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#ff9933' }} />
        </div>
      </div>
    </footer>
  );
}
