import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { PageContainer } from './layout/PageContainer';
import { Loader2 } from 'lucide-react';

export default function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { signUp, startOAuth } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (username.trim().length < 3) {
      setError('Username must be at least 3 characters long');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    const { error: signUpError } = await signUp(username, password);

    if (signUpError) {
      setError(signUpError || 'Failed to create account');
    } else {
      navigate('/login');
    }

    setLoading(false);
  };

  const handleGoogleSignUp = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      const { error } = await startOAuth('google');
      
      if (error) {
        setError(error);
        setGoogleLoading(false);
      }
      // If successful, the user will be redirected to Google
    } catch (err) {
      setError('Failed to start Google Sign Up');
      console.error(err);
      setGoogleLoading(false);
    }
  };



  return (
    <div className="relative min-h-screen w-full bg-gradient-to-br from-[#faf0e2] via-[#ffe9d5] to-[#f7ddc0] text-slate-900 flex items-center justify-center px-4 py-12 overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-20 -top-20 h-64 w-64 rounded-full bg-amber-200 blur-[100px] opacity-70" />
        <div className="absolute right-10 bottom-10 h-52 w-52 rounded-full bg-orange-200 blur-[90px] opacity-70" />
      </div>

      <div className="relative flex justify-center w-full" style={{ maxWidth: 480 }}>
        <Card className="w-full shadow-2xl border-2 border-amber-300/80 bg-white/95 backdrop-blur-sm rounded-2xl p-4 md:p-5">
          <CardHeader className="space-y-3 pb-2 text-center px-8 pt-8">
            <CardTitle className="text-3xl font-bold text-slate-900">Sign Up</CardTitle>
            <CardDescription className="text-base text-slate-600">
              Create your account to get started
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6 px-10 pb-8 w-full">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="username" className="text-slate-900 text-sm font-semibold">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="e.g., vyasa"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                  className="h-11 bg-white border-amber-300 text-slate-900 placeholder:text-slate-400 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/70 focus-visible:border-amber-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-slate-900 text-sm font-semibold">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  className="h-11 bg-white border-amber-300 text-slate-900 placeholder:text-slate-400 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/70 focus-visible:border-amber-400"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-slate-900 text-sm font-semibold">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  className="h-11 bg-white border-amber-300 text-slate-900 placeholder:text-slate-400 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400/70 focus-visible:border-amber-400"
                />
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4 px-10 pb-10 w-full">
              <Button type="submit" className="w-full h-11 bg-[#c75b1a] hover:bg-[#b34d12] text-white font-semibold text-base shadow-md ring-2 ring-amber-200/80" disabled={loading || googleLoading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-slate-300" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-slate-500">Or continue with</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full h-11 border-2 border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-base"
                onClick={handleGoogleSignUp}
                disabled={loading || googleLoading}
              >
                {googleLoading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Connecting to Google...
                  </>
                ) : (
                  <>
                    <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Sign up with Google
                  </>
                )}
              </Button>

              <div className="text-sm text-center text-slate-700">
                Already have an account?{' '}
                <Link to="/login" className="text-[#c75b1a] font-semibold underline">
                  Login
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
