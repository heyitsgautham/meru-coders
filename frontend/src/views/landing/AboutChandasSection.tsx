import type { ReactNode } from "react";
import { KEY_CONCEPTS } from "./landingContent";
import type { KeyConcept } from "./landingContent";
import { BORDER, BRAND, DEVANAGARI_FONT, LandingSection, SectionHeading } from "./LandingParts";

function BodyParagraph({ last = false, children }: { last?: boolean; children: ReactNode }) {
  return (
    <p style={{
      fontSize: '16px',
      color: '#444',
      lineHeight: 1.8,
      ...(last ? {} : { marginBottom: '20px' })
    }}>
      {children}
    </p>
  );
}

function ConceptCard({ concept }: { concept: KeyConcept }) {
  return (
    <div style={{
      backgroundColor: '#faf7f2',
      padding: '24px',
      borderRadius: '12px',
      border: BORDER
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '12px' }}>
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: '10px',
          backgroundColor: concept.tint,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: concept.symbolSize,
          fontWeight: 700,
          color: concept.color
        }}>
          {concept.symbol}
        </div>
        <div>
          <div style={{ fontSize: '18px', fontWeight: 600, color: '#1a1a1a' }}>
            {concept.name}
          </div>
          <div style={{ fontSize: '14px', color: '#888' }}>{concept.gloss}</div>
        </div>
      </div>
      <p style={{ fontSize: '14px', color: '#555', margin: 0, lineHeight: 1.6 }}>
        {concept.description}
      </p>
    </div>
  );
}

/** "What is Chandas?": a short history of Sanskrit prosody and its three key terms. */
export function AboutChandasSection() {
  return (
    <LandingSection id="what-is-chandas" className="landing-section landing-what-is-chandas" background="white">
      <SectionHeading title="What is Chandas?" lead="Understanding the ancient science of Sanskrit prosody" />

      <div className="landing-whatischandas-grid" style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '60px',
        alignItems: 'start'
      }}>
        <div>
          <div style={{
            backgroundColor: '#fff8f0',
            borderLeft: `4px solid ${BRAND}`,
            padding: '24px 28px',
            marginBottom: '32px',
            borderRadius: '0 12px 12px 0'
          }}>
            <p style={{
              fontSize: '20px',
              color: '#4a2c10',
              fontStyle: 'italic',
              margin: 0,
              lineHeight: 1.6,
              fontFamily: DEVANAGARI_FONT
            }}>
              "छन्दः पादौ तु वेदस्य"
            </p>
            <p style={{
              fontSize: '14px',
              color: '#888',
              marginTop: '12px',
              marginBottom: 0
            }}>
              "Chandas is the feet of the Vedas" — Vedāṅga tradition
            </p>
          </div>

          <BodyParagraph>
            <strong>Chandas</strong> (छन्दस्) is the ancient Indian science of prosody—the
            study of poetic meters in Sanskrit literature. It is one of the six Vedāṅgas
            (auxiliary disciplines of the Vedas) and forms the rhythmic foundation of
            all Sanskrit poetry.
          </BodyParagraph>

          <BodyParagraph>
            The foundational text is <strong>Pingala's Chandaḥśāstra</strong> (c. 300-200 BCE),
            which systematically classified meters and introduced concepts that predate
            Western discoveries by centuries—including binary numbers and what we now
            call Pascal's Triangle (known in India as <strong>Meru Prastāra</strong>).
          </BodyParagraph>

          <BodyParagraph last>
            Every Sanskrit verse follows a specific metrical pattern determined by the
            arrangement of <strong>laghu</strong> (light/short) and <strong>guru</strong> (heavy/long)
            syllables. Identifying these patterns is essential for proper pronunciation,
            recitation, and understanding of Sanskrit texts.
          </BodyParagraph>
        </div>

        <div>
          <h3 style={{
            fontSize: '22px',
            fontWeight: 700,
            color: '#1a1a1a',
            marginBottom: '28px'
          }}>
            Key Concepts
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {KEY_CONCEPTS.map((concept) => (
              <ConceptCard key={concept.symbol} concept={concept} />
            ))}
          </div>
        </div>
      </div>
    </LandingSection>
  );
}
