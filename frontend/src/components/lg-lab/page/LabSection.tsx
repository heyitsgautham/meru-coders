import type { ReactNode } from 'react';

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

export { LoadingSpinner };

/** One tab's card: a tinted icon tile, the title and subtitle, then the tab's content. */
export function LabSection({
  icon,
  tint,
  title,
  subtitle,
  children,
}: {
  icon: ReactNode;
  tint: string;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="fade-in section-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '32px' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '16px',
          backgroundColor: tint,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {icon}
        </div>
        <div>
          <h2 style={{
            fontSize: '32px',
            fontWeight: 700,
            color: '#1a1a1a',
            marginBottom: '8px',
            letterSpacing: '-0.5px'
          }}>
            {title}
          </h2>
          <p style={{ fontSize: '16px', color: '#666' }}>
            {subtitle}
          </p>
        </div>
      </div>
      {children}
    </div>
  );
}
