import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { useAuth } from '../contexts/AuthContext';
import { submitContribution } from '../services/api';
import '../styles/contribute.css';

export type ContributionKind = 'verse' | 'meter';

export type ContributionPayload = {
  contribution_type: 'verse' | 'meter_definition';
  data: Record<string, unknown>;
};

export function buildContributionPayload(
  contributionType: ContributionKind,
  data: Record<string, unknown>
): ContributionPayload {
  const normalizedType = contributionType === 'meter' ? 'meter_definition' : 'verse';
  return {
    contribution_type: normalizedType,
    data,
  };
}

export default function ContributionForm() {
  const { user, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const [contributionType, setContributionType] = useState<ContributionKind>('verse');
  const [verseText, setVerseText] = useState('');
  const [meter, setMeter] = useState('');
  const [source, setSource] = useState('');
  const [notes, setNotes] = useState('');
  
  // Meter definition fields
  const [meterName, setMeterName] = useState('');
  const [meterCategory, setMeterCategory] = useState('');
  const [lgPattern, setLgPattern] = useState('');
  const [syllableCount, setSyllableCount] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/login');
    }
  }, [user, authLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      const contributionData = contributionType === 'verse' 
        ? {
            verse_text: verseText,
            meter,
            source,
            notes,
          }
        : {
            meter_name: meterName,
            category: meterCategory,
            lg_pattern: lgPattern,
            syllable_count: syllableCount ? parseInt(syllableCount) : null,
            notes,
          };

      await submitContribution(buildContributionPayload(contributionType, contributionData));

      setSuccess(true);
      
      // Reset form
      setVerseText('');
      setMeter('');
      setSource('');
      setNotes('');
      setMeterName('');
      setMeterCategory('');
      setLgPattern('');
      setSyllableCount('');
      
      // Redirect after 2 seconds
      setTimeout(() => {
        navigate('/profile');
      }, 2000);
      
    } catch (err: any) {
      setError(err.message || 'Failed to submit contribution');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="contribute-page">
      <div className="contribute-shell">
        <button
          type="button"
          className="back-link"
          onClick={() => navigate('/profile')}
        >
          <ArrowLeft size={18} /> Back to profile
        </button>

        <div className="contribute-card">
          <div className="contribute-header">
            <h1 className="contribute-title">Contribute a Shloka</h1>
            <p className="contribute-subtitle">
              Share a verse, meter, or annotation. We review every submission to keep the collection precise.
            </p>
          </div>

          {success && (
            <div className="success-banner" role="status">
              <CheckCircle className="h-4 w-4" />
              <span>Contribution submitted successfully! Redirecting to profile...</span>
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <XCircle className="h-4 w-4" />
              <div>
                <strong className="block">Submission failed</strong>
                <span>{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="form-group">
              <label className="form-label">
                Contribution Type <span className="required">*</span>
              </label>
              <Select
                value={contributionType}
                onValueChange={(value) => setContributionType(value as 'verse' | 'meter')}
                disabled={loading}
              >
                <SelectTrigger className="select-trigger">
                  <SelectValue placeholder="Select contribution type" />
                </SelectTrigger>
                <SelectContent className="select-content">
                  <SelectItem className="select-item" value="verse">Sanskrit Verse</SelectItem>
                  <SelectItem className="select-item" value="meter">Meter Definition</SelectItem>
                </SelectContent>
              </Select>
              <p className="form-helper">
                Choose the closest category. If unsure, pick the most relevant option.
              </p>
            </div>

            {contributionType === 'verse' ? (
              <>
                <div className="form-group">
                  <label className="form-label">
                    Verse (Text) <span className="required">*</span>
                  </label>
                  <Textarea
                    placeholder="Paste the verse here in Devanagari or transliteration"
                    value={verseText}
                    onChange={(e) => setVerseText(e.target.value)}
                    required
                    disabled={loading}
                    className="form-textarea"
                    rows={4}
                  />
                  <p className="form-helper">Multi-line input is supported.</p>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Chandas / Meter Name <span className="required">*</span>
                  </label>
                  <Input
                    placeholder="e.g., अनुष्टुभ्"
                    value={meter}
                    onChange={(e) => setMeter(e.target.value)}
                    required
                    disabled={loading}
                    className="form-input"
                  />
                  <p className="form-helper">Add your best guess; we will verify during review.</p>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Source / Reference <span className="required">*</span>
                  </label>
                  <Input
                    placeholder="e.g., Rigveda 1.1.1, Bhagavad Gita 2.47"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    required
                    disabled={loading}
                    className="form-input"
                  />
                  <p className="form-helper">Citations help us validate quickly.</p>
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">
                    Meter Name (Devanagari) <span className="required">*</span>
                  </label>
                  <Input
                    placeholder="e.g., वसन्ततिलका"
                    value={meterName}
                    onChange={(e) => setMeterName(e.target.value)}
                    required
                    disabled={loading}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Category <span className="required">*</span>
                  </label>
                  <Select
                    value={meterCategory}
                    onValueChange={setMeterCategory}
                    disabled={loading}
                  >
                    <SelectTrigger className="select-trigger">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent className="select-content">
                      <SelectItem className="select-item" value="sama">Sama (Uniform)</SelectItem>
                      <SelectItem className="select-item" value="vishama">Vishama (Varied)</SelectItem>
                      <SelectItem className="select-item" value="ardhasama">Ardhasama (Half-uniform)</SelectItem>
                      <SelectItem className="select-item" value="matra">Matra-based</SelectItem>
                      <SelectItem className="select-item" value="jaati">Jaati-based</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    L-G Pattern <span className="required">*</span>
                  </label>
                  <Input
                    placeholder="e.g., GLGLGLGLGLGLGG"
                    value={lgPattern}
                    onChange={(e) => setLgPattern(e.target.value.toUpperCase())}
                    required
                    disabled={loading}
                    className="form-input"
                  />
                  <p className="form-helper">Use L for Laghu (short) and G for Guru (long).</p>
                </div>

                <div className="form-group">
                  <label className="form-label">Syllable Count</label>
                  <Input
                    type="number"
                    placeholder="e.g., 14"
                    value={syllableCount}
                    onChange={(e) => setSyllableCount(e.target.value)}
                    disabled={loading}
                    className="form-input"
                  />
                  <p className="form-helper">Optional but helps us cross-verify the pattern.</p>
                </div>
              </>
            )}

            <div className="form-group">
              <label className="form-label">Additional Notes</label>
              <Textarea
                placeholder="Add details like manuscript variations, transliteration scheme, or context"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                disabled={loading}
                className="form-textarea tall"
                rows={3}
              />
              <p className="form-helper">The more context you share, the faster we can merge your contribution.</p>
            </div>

            <div className="form-divider" />
            <div className="form-footer">
              <p className="footer-hint">
                We review each submission and may reach out for clarifications.
              </p>
              <button
                type="submit"
                disabled={loading}
                className="submit-button"
              >
                {loading ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Submitting...
                  </span>
                ) : (
                  'Submit Contribution'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
