/** Dark page footer. */
export function LabFooter() {
  return (
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
  );
}
