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

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signInAdmin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { error } = await signInAdmin(username, password);

      if (error) {
        setError(error || 'Invalid credentials');
      } else {
        navigate('/admin');
      }
    } catch (err) {
      setError('An unexpected error occurred');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-gradient-to-br from-[#eef3ff] via-[#dfe8ff] to-[#d4ddff] text-slate-900 flex items-center justify-center px-4 py-12 overflow-hidden">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-16 -top-16 h-64 w-64 rounded-full bg-blue-200 blur-[110px] opacity-70" />
        <div className="absolute right-6 bottom-6 h-52 w-52 rounded-full bg-indigo-200 blur-[90px] opacity-70" />
      </div>

      <div className="relative flex justify-center w-full" style={{ maxWidth: 480 }}>
        <Card className="w-full mx-auto shadow-xl border-2 border-blue-300/80 bg-white/95 backdrop-blur-sm rounded-2xl p-4 md:p-5">
          <CardHeader className="space-y-3 pb-2 text-center px-8 pt-8">
            <CardTitle className="text-3xl font-extrabold text-slate-900">Admin Login</CardTitle>
            <CardDescription className="text-base text-slate-600 font-medium">
              Use the admin username/password to continue
            </CardDescription>
          </CardHeader>

          <form onSubmit={handleSubmit}>
            <CardContent className="space-y-6 px-10 pb-8 w-full">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription className="text-base">{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="username" className="text-slate-900 text-sm font-semibold">Username</Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="admin-erase-sure"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                  className="h-11 bg-white border-blue-300 text-slate-900 placeholder:text-slate-400 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:border-blue-400"
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
                  className="h-11 bg-white border-blue-300 text-slate-900 placeholder:text-slate-400 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400/70 focus-visible:border-blue-400"
                />
              </div>
            </CardContent>

            <CardFooter className="flex flex-col space-y-4 px-10 pb-10 w-full">
              <Button type="submit" className="w-full h-11 bg-[#1d4ed8] hover:bg-[#1a45bd] text-white font-bold text-base shadow-md ring-2 ring-blue-200/80" disabled={loading}>
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Logging in...
                  </>
                ) : (
                  'Login as Admin'
                )}
              </Button>

              <div className="text-sm text-center text-slate-700">
                Go back to{' '}
                <Link to="/login" className="text-[#c75b1a] font-semibold underline">
                  user login
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
