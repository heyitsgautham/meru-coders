import { useNavigate } from "react-router-dom";
import { AboutChandasSection } from "./landing/AboutChandasSection";
import { FeaturesSection, MeterCategoriesSection } from "./landing/CatalogSections";
import { HeroSection, LandingNav } from "./landing/HeroSection";
import { CallToActionSection, LandingFooter, TrustedSourcesSection } from "./landing/ClosingSections";

interface LandingPageProps {
  onLaunchApp?: () => void;
}

/** Public home page; every launch button opens the analyser at /app. */
export function LandingPage({ onLaunchApp: _onLaunchApp }: LandingPageProps) {
  const navigate = useNavigate();
  const launch = () => navigate('/app');

  return (
    <div className="landing-page" style={{
      minHeight: '100vh',
      backgroundColor: '#faf7f2',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
    }}>
      <LandingNav onLaunch={launch} />
      <HeroSection onLaunch={launch} />
      <AboutChandasSection />
      <FeaturesSection onOpenLGLab={() => navigate('/lg-lab')} />
      <MeterCategoriesSection />
      <TrustedSourcesSection />
      <CallToActionSection onLaunch={launch} />
      <LandingFooter />
    </div>
  );
}
