import { useState, useCallback, useEffect } from "react";
import { Header } from "./components/Header";
import { AnalysisForm } from "./components/AnalysisForm";
import { ExamplesView } from "./components/ExamplesView";
import { AboutView } from "./components/AboutView";
import { MandalaBackground } from "./components/MandalaBackground";
import { LandingPage } from "./views/LandingPage";
import type { ViewType } from "./types/api";

const STORAGE_KEY_VIEW = 'chanda_currentView';

export default function App() {
  // Check URL hash to determine which view to show
  const [showLanding, setShowLanding] = useState<boolean>(() => {
    // Show app if hash is #app, otherwise show landing
    return window.location.hash !== '#app';
  });

  const [currentView, setCurrentView] = useState<ViewType>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_VIEW);
    return (saved as ViewType) || "home";
  });
  const [textFromExample, setTextFromExample] = useState("");

  // Handle URL hash changes
  useEffect(() => {
    const handleHashChange = () => {
      if (window.location.hash === '#app') {
        setShowLanding(false);
      } else if (window.location.hash === '' || window.location.hash === '#' || window.location.hash === '#landing') {
        setShowLanding(true);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Save currentView to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_VIEW, currentView);
  }, [currentView]);

  // Handle launching the app from landing page
  const handleLaunchApp = useCallback(() => {
    setShowLanding(false);
    window.location.hash = 'app';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Handle going back to landing page
  const handleGoToLanding = useCallback(() => {
    setShowLanding(true);
    window.location.hash = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Handle example selection - switch to home view and populate text
  const handleSelectExample = useCallback((text: string) => {
    setTextFromExample(text);
    setCurrentView("home");
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // Clear example text when user manually changes it
  const handleTextChange = useCallback(() => {
    // We don't clear it here because we want the form to keep the text
  }, []);

  // Show landing page
  if (showLanding) {
    return <LandingPage onLaunchApp={handleLaunchApp} />;
  }

  // Show main application
  return (
    <div className="min-h-screen relative overflow-hidden flex flex-col">
      {/* Subtle mandala background (very faded) */}
      <div className="fixed inset-0 opacity-[0.03] pointer-events-none">
        <MandalaBackground />
      </div>

      {/* Content - improved vertical centering */}
      <div className="relative z-10 flex-1 flex flex-col">
        <Header 
          currentView={currentView} 
          onViewChange={setCurrentView}
          onGoToLanding={handleGoToLanding}
        />
        
        <main className="flex-1 py-16 px-6">
          {currentView === "home" && (
            <AnalysisForm 
              initialText={textFromExample}
              onTextChange={handleTextChange}
            />
          )}
          {currentView === "examples" && (
            <div style={{ width: '75%', maxWidth: '1400px', margin: '0 auto' }}>
              <ExamplesView onSelectExample={handleSelectExample} />
            </div>
          )}
          {currentView === "about" && (
            <div style={{ width: '1200px', maxWidth: '100%', margin: '0 auto' }}>
              <AboutView />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
