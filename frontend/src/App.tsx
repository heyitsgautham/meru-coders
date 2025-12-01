import { useState, useCallback } from "react";
import { Header } from "./components/Header";
import { AnalysisForm } from "./components/AnalysisForm";
import { ExamplesView } from "./components/ExamplesView";
import { AboutView } from "./components/AboutView";
import { MandalaBackground } from "./components/MandalaBackground";
import type { ViewType } from "./types/api";

export default function App() {
  const [currentView, setCurrentView] = useState<ViewType>("home");
  const [textFromExample, setTextFromExample] = useState("");

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
    <div className="min-h-screen relative overflow-hidden flex flex-col">
      {/* Subtle mandala background (very faded) */}
      <div className="fixed inset-0 opacity-[0.03] pointer-events-none">
        <MandalaBackground />
      </div>

      {/* Content - improved vertical centering */}
      <div className="relative z-10 flex-1 flex flex-col">
        <Header currentView={currentView} onViewChange={setCurrentView} />
        
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
