import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Header } from "../components/Header";
import { AnalysisForm } from "../components/AnalysisForm";
import { SplitViewAnalysis } from "../components/SplitViewAnalysis";
import { ExamplesView } from "../components/ExamplesView";
import { AboutView } from "../components/AboutView";
import { DatasetsView } from "../components/DatasetsView";
import { MandalaBackground } from "../components/MandalaBackground";
import type { ViewType } from "../types/api";

const STORAGE_KEY_VIEW = 'chanda_currentView';

export default function MainApp() {
  const navigate = useNavigate();
  const [currentView, setCurrentView] = useState<ViewType>(() => {
    const saved = localStorage.getItem(STORAGE_KEY_VIEW);
    return (saved as ViewType) || "home";
  });
  const [textFromExample, setTextFromExample] = useState("");

  // Save currentView to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_VIEW, currentView);
  }, [currentView]);

  // Handle going back to landing page
  const handleGoToLanding = useCallback(() => {
    navigate('/');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [navigate]);

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

  return (
    <div className="main-app min-h-screen relative overflow-hidden flex flex-col">
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
        
        <main className="main-content flex-1 py-16 px-6">
          {currentView === "home" && (
            <AnalysisForm
              initialText={textFromExample}
              onTextChange={handleTextChange}
            />
          )}
          {currentView === "splitview" && (
            <SplitViewAnalysis />
          )}
          {currentView === "examples" && (
            <div className="view-container examples-container" style={{ width: '75%', maxWidth: '1400px', margin: '0 auto' }}>
              <ExamplesView onSelectExample={handleSelectExample} />
            </div>
          )}
          {currentView === "datasets" && (
            <div className="view-container datasets-container" style={{ width: '90%', maxWidth: '1600px', margin: '0 auto' }}>
              <DatasetsView />
            </div>
          )}
          {currentView === "about" && (
            <div className="view-container about-container" style={{ width: '1200px', maxWidth: '100%', margin: '0 auto' }}>
              <AboutView />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
