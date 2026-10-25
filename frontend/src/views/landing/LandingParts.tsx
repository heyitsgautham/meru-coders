// Layout pieces shared by the landing page sections.
import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";

export const BRAND = '#c75b1a';
export const BRAND_HOVER = '#b34d12';
export const BORDER = '1px solid #e8e0d5';
export const DEVANAGARI_FONT = "'Noto Sans Devanagari', sans-serif";

interface HoverColorButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  hoverColor: string;
  style: CSSProperties & { backgroundColor: string };
}

/** Button whose background switches to `hoverColor` while the pointer is over it. */
export function HoverColorButton({ hoverColor, style, children, ...rest }: HoverColorButtonProps) {
  return (
    <button
      {...rest}
      style={style}
      onMouseOver={(e) => e.currentTarget.style.backgroundColor = hoverColor}
      onMouseOut={(e) => e.currentTarget.style.backgroundColor = style.backgroundColor}
    >
      {children}
    </button>
  );
}

/** Full-width band with 100px vertical padding that centres a 1200px column. */
export function LandingSection({
  id,
  className = "landing-section",
  background,
  children,
}: {
  id?: string;
  className?: string;
  background: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={className} style={{
      padding: '100px 60px',
      backgroundColor: background,
      display: 'flex',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '1200px'
      }}>
        {children}
      </div>
    </section>
  );
}

/** Centred section title with a one-line lead under it. */
export function SectionHeading({
  title,
  lead,
  leadMaxWidth = '700px',
}: {
  title: string;
  lead: ReactNode;
  leadMaxWidth?: string;
}) {
  return (
    <div style={{
      textAlign: 'center',
      marginBottom: '60px'
    }}>
      <h2 style={{
        fontSize: '40px',
        fontWeight: 700,
        color: '#1a1a1a',
        marginBottom: '20px',
        letterSpacing: '-0.5px'
      }}>
        {title}
      </h2>
      <p style={{
        fontSize: '18px',
        color: '#5a5a5a',
        maxWidth: leadMaxWidth,
        margin: '0 auto',
        lineHeight: 1.7
      }}>
        {lead}
      </p>
    </div>
  );
}

/** Bold card title used by the feature and meter category grids. */
export function CardTitle({ children }: { children: ReactNode }) {
  return (
    <h3 style={{
      fontSize: '18px',
      fontWeight: 700,
      color: '#1a1a1a',
      marginBottom: '12px'
    }}>
      {children}
    </h3>
  );
}

export function CardText({ children }: { children: ReactNode }) {
  return (
    <p style={{
      fontSize: '14px',
      color: '#666',
      lineHeight: 1.6,
      margin: 0
    }}>
      {children}
    </p>
  );
}
