import { ArrowRight } from "lucide-react";
import { BORDER, BRAND, BRAND_HOVER, DEVANAGARI_FONT, HoverColorButton } from "./LandingParts";

/** Fixed top bar with the product name and a launch button. */
export function LandingNav({ onLaunch }: { onLaunch: () => void }) {
  return (
    <nav className="landing-nav" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      height: '70px',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderBottom: BORDER,
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div className="landing-nav-content" style={{
        width: '100%',
        maxWidth: '1200px',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <span className="landing-logo" style={{
          fontSize: '20px',
          fontWeight: 700,
          color: '#4a2c10',
          letterSpacing: '-0.5px'
        }}>
          Meru Coders
        </span>

        <HoverColorButton
          onClick={onLaunch}
          className="landing-launch-btn"
          hoverColor={BRAND_HOVER}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 20px',
            backgroundColor: BRAND,
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          <span className="hidden sm:inline">Launch Application</span>
          <span className="sm:hidden">Launch</span>
          <ArrowRight size={18} />
        </HoverColorButton>
      </div>
    </nav>
  );
}

function SampleStat({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{
      backgroundColor: '#f8f9fa',
      padding: '16px',
      borderRadius: '8px'
    }}>
      <div style={{ fontSize: '12px', color: '#888', marginBottom: '4px' }}>
        {label}
      </div>
      <div style={{ fontSize: '18px', fontWeight: 600, color }}>
        {value}
      </div>
    </div>
  );
}

/** Static example of what an identification result looks like. */
function SampleCard() {
  return (
    <div className="landing-sample-card" style={{
      backgroundColor: 'white',
      borderRadius: '16px',
      padding: '24px',
      boxShadow: '0 4px 40px rgba(0, 0, 0, 0.08)',
      border: BORDER
    }}>
      <div style={{
        fontSize: '13px',
        fontWeight: 600,
        color: '#888',
        marginBottom: '16px',
        letterSpacing: '1px'
      }}>
        SAMPLE INPUT
      </div>

      <div style={{
        backgroundColor: '#fffbf5',
        padding: '20px',
        borderRadius: '12px',
        marginBottom: '24px',
        border: BORDER
      }}>
        <p style={{
          fontSize: '22px',
          color: '#4a2c10',
          fontFamily: DEVANAGARI_FONT,
          lineHeight: 1.6,
          margin: 0
        }}>
          धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः<br />
          मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय
        </p>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '20px'
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          backgroundColor: '#d4edda',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#28a745" strokeWidth="3">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <span style={{
          fontSize: '20px',
          fontWeight: 700,
          color: '#1a1a1a'
        }}>
          अनुष्टुभ् (Anuṣṭubh)
        </span>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px'
      }}>
        <SampleStat label="Syllables" value="32 (8×4)" color="#1a1a1a" />
        <SampleStat label="Confidence" value="High" color="#28a745" />
      </div>
    </div>
  );
}

/** Headline, call to action and the sample result card. */
export function HeroSection({ onLaunch }: { onLaunch: () => void }) {
  return (
    <section className="landing-section landing-hero" style={{
      paddingTop: '120px',
      paddingBottom: '60px',
      paddingLeft: '24px',
      paddingRight: '24px',
      display: 'flex',
      justifyContent: 'center'
    }}>
      <div className="landing-hero-grid" style={{
        width: '100%',
        maxWidth: '1200px',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gap: '40px',
        alignItems: 'center'
      }}>
        <div className="landing-hero-text">
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
              color: BRAND,
              letterSpacing: '0.5px'
            }}>
              SANSKRIT PROSODY TOOL
            </span>
          </div>

          <h1 className="landing-hero-title" style={{
            fontSize: '36px',
            fontWeight: 700,
            color: '#1a1a1a',
            lineHeight: 1.15,
            marginBottom: '20px',
            letterSpacing: '-1px'
          }}>
            Identify Sanskrit{' '}
            <span style={{ color: BRAND }}>Meters</span>{' '}
            Instantly
          </h1>

          <p className="landing-hero-subtitle" style={{
            fontSize: '16px',
            color: '#5a5a5a',
            lineHeight: 1.7,
            marginBottom: '32px',
            maxWidth: '480px'
          }}>
            A powerful tool for identifying the <em>chandas</em> (metrical patterns)
            of Sanskrit verses. Built on Pingala's ancient prosodic system with
            a database of over 1,900 meters.
          </p>

          <div className="landing-hero-buttons" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <HoverColorButton
              onClick={onLaunch}
              hoverColor={BRAND_HOVER}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                padding: '14px 28px',
                backgroundColor: BRAND,
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                width: '100%'
              }}
            >
              Get Started
              <ArrowRight size={20} />
            </HoverColorButton>

            <a
              href="#what-is-chandas"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '14px 28px',
                backgroundColor: 'transparent',
                color: '#4a2c10',
                border: '2px solid #d4c4b0',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'none',
                transition: 'all 0.2s ease',
                width: '100%'
              }}
            >
              Learn More
            </a>
          </div>
        </div>

        <SampleCard />
      </div>
    </section>
  );
}
