import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { IdentifyResponse } from '../types/api';
import * as api from '../services/api';
import { AnalysisForm } from './AnalysisForm';

vi.mock('../services/api', () => ({
  getAPIInfo: vi.fn(),
  identifyFromText: vi.fn(),
  identifyDandaka: vi.fn(),
  extractTextFromImage: vi.fn(),
  extractTextFromFile: vi.fn(),
  extractTextFromAudio: vi.fn(),
  validateSloka: vi.fn(),
}));

// The result views have their own tests; here they only need to show that a result arrived.
vi.mock('./ResultsDisplay', () => ({
  ResultsDisplay: ({ result }: { result: IdentifyResponse }) => (
    <div data-testid="results">{result.result?.line?.[0]?.result?.display_chanda}</div>
  ),
}));
vi.mock('./DandakaResultsDisplay', () => ({
  DandakaResultsDisplay: () => <div data-testid="dandaka-results" />,
}));
vi.mock('./PingalaAcharyaSpeaker', () => ({
  PingalaAcharyaSpeaker: () => <div data-testid="pingala" />,
}));

const mocked = vi.mocked(api);
const VERSE = 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः';

function identified(found: boolean, meter = 'अनुष्टुभ्'): IdentifyResponse {
  return { success: true, result: { line: [{ result: { found, display_chanda: meter } }] } } as unknown as IdentifyResponse;
}

function upload(input: HTMLElement, file: File) {
  return userEvent.upload(input as HTMLInputElement, file, { applyAccept: false });
}

function fileInput(accept: string): HTMLElement {
  const input = document.querySelector(`input[type=file][accept="${accept}"]`);
  if (!input) throw new Error(`no file input accepting ${accept}`);
  return input as HTMLElement;
}

beforeEach(() => {
  vi.resetAllMocks();
  mocked.getAPIInfo.mockResolvedValue({ name: 'api' } as never);
  mocked.identifyFromText.mockResolvedValue(identified(true));
  Element.prototype.scrollIntoView = vi.fn();
  vi.spyOn(window, 'alert').mockImplementation(() => {});
});

describe('AnalysisForm text tab', () => {
  it('identifies typed text in auto mode and shows the result with Pingala', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm />);

    await user.type(screen.getByPlaceholderText(/Type or paste your Sanskrit shloka/), VERSE);
    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));

    expect(await screen.findByTestId('results')).toHaveTextContent('अनुष्टुभ्');
    expect(mocked.identifyFromText).toHaveBeenCalledWith(VERSE, 'verse', '', 'auto');
    expect(screen.getByTestId('pingala')).toBeInTheDocument();
  });

  it('sends the selected identification mode', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm initialText={VERSE} />);

    await user.click(screen.getByRole('button', { name: 'Vedic Mode' }));
    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));

    await waitFor(() => expect(mocked.identifyFromText).toHaveBeenCalledWith(VERSE, 'verse', '', 'vedic'));
  });

  it('uses the Daṇḍaka endpoint in Daṇḍaka mode and skips Pingala', async () => {
    mocked.identifyDandaka.mockResolvedValue({ success: true, result: { mode: 'dandaka' } } as never);
    const user = userEvent.setup();
    render(<AnalysisForm initialText={VERSE} />);

    await user.click(screen.getByRole('button', { name: 'Daṇḍaka / Stotra' }));
    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));

    expect(await screen.findByTestId('dandaka-results')).toBeInTheDocument();
    expect(mocked.identifyDandaka).toHaveBeenCalledWith(VERSE);
    expect(mocked.identifyFromText).not.toHaveBeenCalled();
    expect(screen.queryByTestId('pingala')).not.toBeInTheDocument();
  });

  it('asks for text instead of calling the API when the box is empty', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm />);

    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));

    expect(window.alert).toHaveBeenCalledWith('Please enter some Sanskrit text');
    expect(mocked.identifyFromText).not.toHaveBeenCalled();
  });

  it('does not summon Pingala when no meter was found', async () => {
    mocked.identifyFromText.mockResolvedValue(identified(false, ''));
    const user = userEvent.setup();
    render(<AnalysisForm initialText={VERSE} />);

    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));

    expect(await screen.findByTestId('results')).toBeInTheDocument();
    expect(screen.queryByTestId('pingala')).not.toBeInTheDocument();
  });

  it('shows the API error under the form', async () => {
    mocked.identifyFromText.mockRejectedValue(new Error('Rate limit exceeded'));
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<AnalysisForm initialText={VERSE} />);

    await user.click(screen.getByRole('button', { name: 'Identify Chanda' }));

    expect(await screen.findByText('Rate limit exceeded')).toBeInTheDocument();
    expect(screen.queryByTestId('results')).not.toBeInTheDocument();
  });

  it('identifies on its own when the parent passes autoIdentify', async () => {
    render(<AnalysisForm initialText={VERSE} autoIdentify />);
    expect(await screen.findByTestId('results', {}, { timeout: 2000 })).toBeInTheDocument();
    expect(mocked.identifyFromText).toHaveBeenCalledTimes(1);
  });

  it('warns when the backend is unreachable', async () => {
    mocked.getAPIInfo.mockRejectedValue(new Error('offline'));
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    render(<AnalysisForm />);
    expect(await screen.findByText('Backend API not connected')).toBeInTheDocument();
  });
});

describe('AnalysisForm tabs', () => {
  it('restores the tab from the previous visit and remembers a new choice', async () => {
    localStorage.setItem('chanda_activeTab', 'voice');
    const user = userEvent.setup();
    render(<AnalysisForm />);

    expect(screen.getByText('Record or Upload Sanskrit Chanting')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'File Upload' }));

    expect(screen.getByText('Upload Document File')).toBeInTheDocument();
    expect(localStorage.getItem('chanda_activeTab')).toBe('file');
  });

  it('hides the mode selector away from the text tab', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm />);
    await user.click(screen.getByRole('button', { name: 'Image OCR' }));
    expect(screen.queryByRole('button', { name: 'Vedic Mode' })).not.toBeInTheDocument();
  });
});

describe('AnalysisForm image tab', () => {
  beforeEach(() => localStorage.setItem('chanda_activeTab', 'image'));

  it('extracts text from an image and identifies it on the text tab', async () => {
    mocked.extractTextFromImage.mockResolvedValue({ success: true, text: VERSE } as never);
    const user = userEvent.setup();
    render(<AnalysisForm />);

    const image = new File(['png'], 'verse.png', { type: 'image/png' });
    await upload(fileInput('image/*'), image);
    expect(await screen.findByText('verse.png')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Extract Text' }));
    expect(await screen.findByText(VERSE)).toBeInTheDocument();
    expect(mocked.extractTextFromImage).toHaveBeenCalledWith(image);

    await user.click(screen.getByRole('button', { name: 'Identify Chandas' }));
    expect(await screen.findByTestId('results')).toBeInTheDocument();
    expect(mocked.identifyFromText).toHaveBeenCalledWith(VERSE, 'verse', '', 'auto');
    expect(screen.getByPlaceholderText(/Type or paste/)).toHaveValue(VERSE);
  });

  it('rejects a file that is not an image', async () => {
    render(<AnalysisForm />);
    await upload(fileInput('image/*'), new File(['%PDF'], 'verse.pdf', { type: 'application/pdf' }));
    expect(window.alert).toHaveBeenCalledWith('Please select an image file');
    expect(screen.queryByText('verse.pdf')).not.toBeInTheDocument();
  });

  it('clears the image with the remove button', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm />);
    await upload(fileInput('image/*'), new File(['png'], 'verse.png', { type: 'image/png' }));
    await screen.findByText('verse.png');

    await user.click(screen.getByTitle('Remove image'));
    expect(screen.queryByText('verse.png')).not.toBeInTheDocument();
    expect(screen.getByText('Drop your image here')).toBeInTheDocument();
  });
});

describe('AnalysisForm file tab', () => {
  beforeEach(() => localStorage.setItem('chanda_activeTab', 'file'));

  it('extracts a document, shows its type, page count and warnings, then identifies it', async () => {
    mocked.extractTextFromFile.mockResolvedValue({
      success: true,
      text: VERSE,
      file_info: { file_type: 'docx', page_count: 3 },
      warnings: ['Some characters used CID encoding'],
    } as never);
    const user = userEvent.setup();
    render(<AnalysisForm />);

    await upload(fileInput('.docx,.txt,.text'), new File([VERSE], 'gita.docx'));
    expect(await screen.findByText('gita.docx')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Extract Text' }));
    expect(await screen.findByText('Word Document')).toBeInTheDocument();
    expect(screen.getByText('3 pages')).toBeInTheDocument();
    expect(screen.getByText('Some characters used CID encoding')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Identify Chandas' }));
    expect(await screen.findByTestId('results')).toBeInTheDocument();
    expect(mocked.identifyFromText).toHaveBeenCalledWith(VERSE, 'verse', '', 'auto');
  });

  it('shows why extraction failed', async () => {
    mocked.extractTextFromFile.mockRejectedValue(new Error('Could not read the document'));
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<AnalysisForm />);

    await upload(fileInput('.docx,.txt,.text'), new File([VERSE], 'gita.txt'));
    await user.click(await screen.findByRole('button', { name: 'Extract Text' }));

    expect(await screen.findByText('Extraction Failed')).toBeInTheDocument();
  });

  it('rejects an unsupported document type', async () => {
    render(<AnalysisForm />);
    await upload(fileInput('.docx,.txt,.text'), new File(['%PDF'], 'gita.pdf'));
    expect(window.alert).toHaveBeenCalledWith('Please select a DOCX or TXT file');
  });
});

describe('AnalysisForm voice tab', () => {
  beforeEach(() => {
    localStorage.setItem('chanda_activeTab', 'voice');
    mocked.extractTextFromAudio.mockResolvedValue({ success: true, text: 'धर्मक्षेत्रे कुरुक्षेत्रे' } as never);
  });

  async function transcribe() {
    const user = userEvent.setup();
    render(<AnalysisForm />);
    await upload(fileInput('.wav,.mp3,.webm,.ogg,.m4a,.flac'), new File(['mp3'], 'chant.mp3'));
    await user.click(await screen.findByRole('button', { name: 'Extract Text' }));
    await screen.findByText('Transcribed Text');
    return user;
  }

  it('replaces the transcript with the verified verse at 90% similarity or more', async () => {
    mocked.validateSloka.mockResolvedValue({
      success: true,
      found: true,
      is_valid: false,
      similarity: 0.95,
      original_text: VERSE,
      difference_count: 2,
    });
    const user = await transcribe();

    await user.click(screen.getByRole('button', { name: /NORMALIZE/ }));

    expect(await screen.findByText('Normalised')).toBeInTheDocument();
    expect(screen.getByText('2 differences corrected')).toBeInTheDocument();
    expect(screen.getByText(VERSE)).toBeInTheDocument();
    expect(mocked.validateSloka).toHaveBeenCalledWith('धर्मक्षेत्रे कुरुक्षेत्रे');
  });

  it('keeps the transcript when the best match is below 90%', async () => {
    mocked.validateSloka.mockResolvedValue({
      success: true,
      found: true,
      similarity: 0.7,
      similarity_percentage: 70.04,
      original_text: VERSE,
    });
    const user = await transcribe();

    await user.click(screen.getByRole('button', { name: /NORMALIZE/ }));

    expect(await screen.findByText('Similarity Too Low')).toBeInTheDocument();
    expect(screen.getByText(/70\.0% similarity/)).toBeInTheDocument();
    expect(screen.getByText('धर्मक्षेत्रे कुरुक्षेत्रे')).toBeInTheDocument();
  });

  it('says so when no verified verse matches', async () => {
    mocked.validateSloka.mockResolvedValue({ success: true, found: false });
    const user = await transcribe();
    await user.click(screen.getByRole('button', { name: /NORMALIZE/ }));
    expect(await screen.findByText('No Match Found')).toBeInTheDocument();
  });

  it('identifies the transcript as-is on the text tab', async () => {
    const user = await transcribe();
    await user.click(screen.getByRole('button', { name: 'USE AS-IS' }));
    await user.click(screen.getByRole('button', { name: 'Identify Chandas' }));

    expect(await screen.findByTestId('results')).toBeInTheDocument();
    expect(mocked.identifyFromText).toHaveBeenCalledWith('धर्मक्षेत्रे कुरुक्षेत्रे', 'verse', '', 'auto');
  });

  it('shows a transcription failure', async () => {
    mocked.extractTextFromAudio.mockRejectedValue(new Error('ASR service unavailable'));
    vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<AnalysisForm />);
    await upload(fileInput('.wav,.mp3,.webm,.ogg,.m4a,.flac'), new File(['mp3'], 'chant.mp3'));
    await user.click(await screen.findByRole('button', { name: 'Extract Text' }));

    expect(await screen.findByText('Transcription Failed')).toBeInTheDocument();
  });

  it('rejects an unsupported audio format', async () => {
    render(<AnalysisForm />);
    await upload(fileInput('.wav,.mp3,.webm,.ogg,.m4a,.flac'), new File(['x'], 'chant.aiff'));
    expect(window.alert).toHaveBeenCalledWith('Please select a WAV or MP3 audio file');
  });
});
