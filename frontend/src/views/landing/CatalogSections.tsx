import { ArrowRight, Atom, BookOpen, Database, Sparkles, Zap } from "lucide-react";
import type { ReactNode } from "react";
import { FEATURES, METER_CATEGORIES } from "./landingContent";
import type { FeatureIcon } from "./landingContent";
import {
  BORDER,
  BRAND,
  BRAND_HOVER,
  CardText,
  CardTitle,
  HoverColorButton,
  LandingSection,
  SectionHeading,
} from "./LandingParts";

const FEATURE_ICONS: Record<FeatureIcon, ReactNode> = {
  database: <Database size={28} />,
  zap: <Zap size={28} />,
  book: <BookOpen size={28} />,
  sparkles: <Sparkles size={28} />,
};

const FOUR_COLUMNS = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: '24px'
} as const;

/** Call-out that links to the L-G Laboratory. */
export function LGLabHighlight({ onOpen }: { onOpen: () => void }) {
  return (
    <div data-testid="lg-lab-highlight" style={{
      marginTop: '48px',
      background: 'linear-gradient(135deg, #fff3e6 0%, #ffe8cc 100%)',
      padding: '40px',
      borderRadius: '16px',
      border: '2px solid #ffd699',
      boxShadow: '0 4px 20px rgba(199, 91, 26, 0.15)'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '32px',
        maxWidth: '900px',
        margin: '0 auto'
      }}>
        <div style={{
          width: '80px',
          height: '80px',
          borderRadius: '20px',
          background: 'linear-gradient(135deg, #ff9933 0%, #c75b1a 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 15px rgba(199, 91, 26, 0.3)',
          flexShrink: 0
        }}>
          <Atom size={40} color="white" />
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{
            fontSize: '24px',
            fontWeight: 700,
            color: '#4a2c10',
            marginBottom: '12px'
          }}>
            🔬 L-G Laboratory
          </h3>
          <p style={{
            fontSize: '16px',
            color: '#555',
            lineHeight: 1.7,
            marginBottom: '16px'
          }}>
            Discover the deep connections between Laghu-Guru patterns and the rhythms of nature,
            mathematics, music, and human consciousness. Explore interactive visualizations of
            Fibonacci sequences, breath patterns, and natural rhythms.
          </p>
          <HoverColorButton
            onClick={onOpen}
            hoverColor={BRAND_HOVER}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              backgroundColor: BRAND,
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '15px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            Explore L-G Lab
            <ArrowRight size={18} />
          </HoverColorButton>
        </div>
      </div>
    </div>
  );
}

/** Four feature cards and the L-G Laboratory call-out. */
export function FeaturesSection({ onOpenLGLab }: { onOpenLGLab: () => void }) {
  return (
    <LandingSection background="#faf7f2">
      <SectionHeading
        title="Features"
        lead="Everything you need for Sanskrit meter identification"
        leadMaxWidth="600px"
      />

      <div className="landing-features-grid" style={FOUR_COLUMNS}>
        {FEATURES.map((feature) => (
          <div key={feature.title} style={{
            backgroundColor: 'white',
            padding: '32px',
            borderRadius: '16px',
            border: BORDER,
            textAlign: 'center',
            transition: 'all 0.2s ease'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              backgroundColor: '#fff3e6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px',
              color: BRAND
            }}>
              {FEATURE_ICONS[feature.icon]}
            </div>
            <CardTitle>{feature.title}</CardTitle>
            <CardText>{feature.description}</CardText>
          </div>
        ))}
      </div>

      <LGLabHighlight onOpen={onOpenLGLab} />
    </LandingSection>
  );
}

/** Counts of meters per category in the database. */
export function MeterCategoriesSection() {
  return (
    <LandingSection background="white">
      <SectionHeading
        title="Meter Categories"
        lead="Our database covers all major categories of Sanskrit meters"
      />

      <div className="landing-meters-grid" style={FOUR_COLUMNS}>
        {METER_CATEGORIES.map((category) => (
          <div key={category.name} style={{
            backgroundColor: '#faf7f2',
            padding: '32px',
            borderRadius: '16px',
            border: BORDER
          }}>
            <div style={{
              fontSize: '48px',
              fontWeight: 700,
              color: category.color,
              marginBottom: '8px'
            }}>
              {category.count}
            </div>
            <CardTitle>{category.name}</CardTitle>
            <CardText>{category.description}</CardText>
          </div>
        ))}
      </div>
    </LandingSection>
  );
}
