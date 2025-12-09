import { Home, User, LogIn, Users, Gamepad2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import type { ViewType } from "../types/api";

interface HeaderProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  onGoToLanding?: () => void;
}

export function Header({ currentView, onViewChange, onGoToLanding }: HeaderProps) {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  
  const navItems: { name: string; view: ViewType }[] = [
    { name: 'Home', view: 'home' },
    { name: 'Split View', view: 'splitview' },
    { name: 'Examples', view: 'examples' },
    { name: 'Datasets', view: 'datasets' },
    { name: 'About', view: 'about' }
  ];

  const handleProfileClick = () => {
    if (isAdmin) {
      navigate('/admin');
    } else {
      navigate('/profile');
    }
  };

  const handleCommunityClick = () => {
    navigate('/community');
  };

  const handleGameClick = () => {
    // Open the game in a new tab/window
    window.open('http://localhost:9000', '_blank');
  };

  return (
    <header className="app-header bg-white sticky top-0 z-50 transition-all duration-300 shadow-sm" style={{ width: '100%' }}>
      <div className="app-header-inner" style={{ width: '100%', padding: '16px 15px' }}>
        <div className="app-header-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
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
              className="cursor-pointer app-logo"
              onClick={() => onViewChange('home')}
            >
              <span style={{ fontSize: '1.75rem', fontWeight: 'bold', color: '#4a2c10' }}>Meru Coders</span>
            </div>
          </div>

          {/* Navigation - consistent pill style with proper spacing */}
          <nav className="app-nav flex items-center gap-3 bg-[#fdf8f3] px-4 py-2 rounded-full border border-[var(--color-border-subtle)]">
            {navItems.map((item) => (
              <button
                key={item.view}
                onClick={() => onViewChange(item.view)}
                className={`nav-link ${currentView === item.view ? 'active' : ''}`}
              >
                {item.name}
              </button>
            ))}
            
            {/* Game Link */}
            <button
              onClick={handleGameClick}
              className="nav-link flex items-center gap-1"
              title="Play Chandas Learning Game"
            >
              <Gamepad2 className="w-4 h-4" />
              <span className="nav-link-text">Game</span>
            </button>
            
            {/* Community Link */}
            <button
              onClick={handleCommunityClick}
              className={`nav-link flex items-center gap-1 ${currentView === 'community' ? 'active' : ''}`}
            >
              <Users className="w-4 h-4" />
              <span className="nav-link-text">Community</span>
            </button>
            
            {/* Auth Navigation */}
            {user ? (
              <button
                onClick={handleProfileClick}
                className="nav-link flex items-center gap-1"
              >
                <User className="w-4 h-4" />
                <span className="nav-link-text">{isAdmin ? 'Admin' : 'Profile'}</span>
              </button>
            ) : (
              <Link
                to="/login"
                className="nav-link flex items-center gap-1"
              >
                <LogIn className="w-4 h-4" />
                <span className="nav-link-text">Login</span>
              </Link>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}