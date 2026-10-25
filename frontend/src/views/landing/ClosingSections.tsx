import { ArrowRight } from "lucide-react";
import type { MouseEvent } from "react";
import { TRUSTED_SOURCES } from "./landingContent";
import type { TrustedSource } from "./landingContent";
import { BORDER, BRAND, DEVANAGARI_FONT, HoverColorButton, LandingSection, SectionHeading } from "./LandingParts";

const CARD_SHADOW = '0 2px 12px rgba(0, 0, 0, 0.04)';
const CARD_SHADOW_RAISED = '0 8px 30px rgba(0, 0, 0, 0.1)';

function raise(e: MouseEvent<HTMLDivElement>) {
  e.currentTarget.style.transform = 'translateY(-4px)';
  e.currentTarget.style.boxShadow = CARD_SHADOW_RAISED;
}

function lower(e: MouseEvent<HTMLDivElement>) {
  e.currentTarget.style.transform = 'translateY(0)';
  e.currentTarget.style.boxShadow = CARD_SHADOW;
}

/** Book cover card that lifts while hovered. */
function SourceCard({ source }: { source: TrustedSource }) {
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '16px',
      overflow: 'hidden',
      border: BORDER,
      transition: 'all 0.3s ease',
      boxShadow: CARD_SHADOW
    }}
    onMouseOver={raise}
    onMouseOut={lower}
    >
      <div style={{
        aspectRatio: '3/4',
        overflow: 'hidden',
        backgroundColor: '#f5f0e8'
      }}>
        <img
          src={source.image}
          alt={source.title}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${source.scale})`,
            transition: 'transform 0.3s ease'
          }}
        />
      </div>
      <div style={{
        padding: '24px',
        textAlign: 'center'
      }}>
        <h3 style={{
          fontSize: '18px',
          fontWeight: 700,
          color: '#1a1a1a',
          marginBottom: '4px'
        }}>
          {source.title}
        </h3>
        <p style={{
          fontSize: '16px',
          color: BRAND,
          fontFamily: DEVANAGARI_FONT,
          marginBottom: '12px'
        }}>
          {source.subtitle}
        </p>
        <p style={{
          fontSize: '13px',
          color: '#666',
          lineHeight: 1.5,
          margin: 0
        }}>
          {source.description}
        </p>
      </div>
    </div>
  );
}

/** The four texts the meter database was validated against. */
export function TrustedSourcesSection() {
  return (
    <LandingSection background="#faf7f2">
      <SectionHeading
        title="Trusted Sources"
        lead={
          <>
            Our dataset has been meticulously collected and validated using these authoritative
            texts—the foundational scriptures of Sanskrit literature and prosody.
          </>
        }
      />

      <div className="trusted-sources-grid">
        {TRUSTED_SOURCES.map((source) => (
          <SourceCard key={source.title} source={source} />
        ))}
      </div>

      <div style={{
        marginTop: '48px',
        textAlign: 'center',
        padding: '24px 40px',
        backgroundColor: 'white',
        borderRadius: '12px',
        border: BORDER
      }}>
        <p style={{
          fontSize: '15px',
          color: '#555',
          lineHeight: 1.7,
          margin: 0
        }}>
          <span style={{ fontWeight: 600, color: '#4a2c10' }}>Scholarly Validation:</span>{' '}
          Each meter in our database has been cross-referenced with multiple authoritative sources
          to ensure accuracy and authenticity in identification.
        </p>
      </div>
    </LandingSection>
  );
}

/** Dark closing band with the final launch button. */
export function CallToActionSection({ onLaunch }: { onLaunch: () => void }) {
  return (
    <section className="landing-section landing-cta" style={{
      padding: '100px 60px',
      backgroundColor: '#4a2c10',
      display: 'flex',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '800px',
        textAlign: 'center'
      }}>
        <h2 className="landing-cta-title" style={{
          fontSize: '40px',
          fontWeight: 700,
          color: 'white',
          marginBottom: '20px',
          letterSpacing: '-0.5px'
        }}>
          Ready to Identify Sanskrit Meters?
        </h2>
        <p style={{
          fontSize: '18px',
          color: 'rgba(255, 255, 255, 0.8)',
          marginBottom: '40px',
          lineHeight: 1.7
        }}>
          Start analyzing Sanskrit verses with our comprehensive meter identification tool.
          Free to use, no registration required.
        </p>
        <HoverColorButton
          onClick={onLaunch}
          className="landing-cta-btn"
          hoverColor="#d96b2a"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '12px',
            padding: '18px 40px',
            backgroundColor: BRAND,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '18px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          Launch Application
          <ArrowRight size={22} />
        </HoverColorButton>
      </div>
    </section>
  );
}

export function LandingFooter() {
  return (
    <footer className="landing-footer" style={{
      padding: '40px 60px',
      backgroundColor: '#3a2210',
      display: 'flex',
      justifyContent: 'center'
    }}>
      <div className="landing-footer-content" style={{
        width: '100%',
        maxWidth: '1200px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{
          fontSize: '18px',
          fontWeight: 600,
          color: 'white'
        }}>
          Meru Coders
        </span>
        <span style={{
          fontSize: '14px',
          color: 'rgba(255, 255, 255, 0.6)'
        }}>
          Sanskrit Meter Identification Tool
        </span>
      </div>
    </footer>
  );
}
