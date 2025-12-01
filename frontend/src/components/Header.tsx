import type { ViewType } from "../types/api";

interface HeaderProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
}

export function Header({ currentView, onViewChange }: HeaderProps) {
  const navItems: { name: string; view: ViewType }[] = [
    { name: 'Home', view: 'home' },
    { name: 'Examples', view: 'examples' },
    { name: 'About', view: 'about' }
  ];

  return (
    <header className="border-b border-[#e5d4bf] bg-white sticky top-0 z-50 transition-all duration-300 shadow-sm">
      <div className="container mx-auto px-10 py-4">
        <div className="flex items-center justify-between">
          {/* Logo - Meru Coders */}
          <div 
            className="cursor-pointer"
            onClick={() => onViewChange('home')}
          >
            <span style={{ fontSize: '1.75rem', fontWeight: 'bold', color: '#4a2c10' }}>Meru Coders</span>
          </div>

          {/* Navigation - consistent pill style with proper spacing */}
          <nav className="flex items-center gap-3 pr-6 bg-[#fdf8f3] px-4 py-2 rounded-full border border-[var(--color-border-subtle)]">
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