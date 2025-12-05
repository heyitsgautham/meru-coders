import { Home } from "lucide-react";
import type { ViewType } from "../types/api";

interface HeaderProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  onGoToLanding?: () => void;
}

export function Header({ currentView, onViewChange, onGoToLanding }: HeaderProps) {
  const navItems: { name: string; view: ViewType }[] = [
    { name: 'Home', view: 'home' },
    { name: 'Examples', view: 'examples' },
    { name: 'Datasets', view: 'datasets' },
    { name: 'About', view: 'about' }
  ];

  return (
    <header className="bg-white sticky top-0 z-50 transition-all duration-300 shadow-sm" style={{ width: '100%' }}>
      <div style={{ width: '100%', padding: '16px 15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          {/* Logo - Meru Coders with optional back to landing */}
          <div className="flex items-center gap-3">
            {onGoToLanding && (
              <button
                onClick={onGoToLanding}
                className="p-2 rounded-lg hover:bg-[var(--color-primary-soft)] transition-colors"
                title="Back to Landing Page"
              >
                <Home className="w-5 h-5 text-[var(--color-text-muted)]" />
              </button>
            )}
            <div 
              className="cursor-pointer"
              onClick={() => onViewChange('home')}
            >
              <span style={{ fontSize: '1.75rem', fontWeight: 'bold', color: '#4a2c10' }}>Meru Coders</span>
            </div>
          </div>

          {/* Navigation - consistent pill style with proper spacing */}
          <nav className="flex items-center gap-3 bg-[#fdf8f3] px-4 py-2 rounded-full border border-[var(--color-border-subtle)]">
            {navItems.map((item) => (
              <button
                key={item.view}
                onClick={() => onViewChange(item.view)}
                className={`nav-link ${currentView === item.view ? 'active' : ''}`}
              >
                {item.name}
              </button>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}