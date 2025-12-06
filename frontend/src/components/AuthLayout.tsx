import { ReactNode } from 'react';
import '../styles/auth.css';

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
  showBrand?: boolean;
}

export function AuthLayout({ title, subtitle, children, showBrand = true }: AuthLayoutProps) {
  return (
    <div className="auth-page">
      <div className="auth-card" role="form" aria-label={title}>
        {showBrand && <div className="auth-brand">Meru Coders</div>}
        <h1 className="auth-title">{title}</h1>
        <p className="auth-subtitle">{subtitle}</p>
        <div className="auth-form">
          {children}
        </div>
      </div>
    </div>
  );
}

export default AuthLayout;
