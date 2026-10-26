import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { IdentifyResponse } from '../types/api';
import fixture from '../test/fixtures/identify-gita-1-1.json';
import { ResultsDisplay } from './ResultsDisplay';

vi.mock('./TextToSpeech', () => ({
  TextToSpeech: ({ text }: { text: string }) => <div data-testid="tts">{text}</div>,
}));

const GITA = fixture as unknown as IdentifyResponse;

function linesOnly(): IdentifyResponse {
  const copy = structuredClone(GITA);
  copy.result!.verse = [];
  delete copy.summary;
  return copy;
}

beforeEach(() => vi.spyOn(console, 'log').mockImplementation(() => {}));

describe('ResultsDisplay', () => {
  it('leads with the verse meter and its confidence', () => {
    render(<ResultsDisplay result={GITA} type="text" />);
    expect(screen.getAllByRole('heading', { name: 'अनुष्टुभ्' })[0]).toBeInTheDocument();
    expect(screen.getAllByText('Very High').length).toBeGreaterThan(0);
    expect(screen.getByText('Line-by-Line Analysis (Pāda Details)')).toBeInTheDocument();
  });

  it('links the download to the saved result', () => {
    render(<ResultsDisplay result={GITA} type="text" />);
    expect(screen.getByRole('link', { name: /Download Results/ })).toHaveAttribute(
      'href',
      'http://localhost:5000/api/download/result_6d480555f18c2dc759edc916c7746aa3_1_1.json',
    );
  });

  it('offers the typed verse for recitation', () => {
    render(<ResultsDisplay result={GITA} type="text" />);
    expect(screen.getByTestId('tts')).toHaveTextContent('धर्मक्षेत्रे कुरुक्षेत्रे');
  });

  it('switches the line analysis to IAST and back', async () => {
    const user = userEvent.setup();
    render(<ResultsDisplay result={GITA} type="text" />);
    await user.click(screen.getByRole('button', { name: 'Show IAST (English)' }));
    expect(screen.getByRole('button', { name: 'Show Devanagari' })).toBeInTheDocument();
  });

  it('shows the line meter when there is no verse result', () => {
    render(<ResultsDisplay result={linesOnly()} type="text" />);
    expect(screen.getByText('Line-by-Line Analysis')).toBeInTheDocument();
    expect(screen.queryByText('Line-by-Line Analysis (Pāda Details)')).not.toBeInTheDocument();
  });

  it('hides the syllable overview in the compact split view', () => {
    const { rerender } = render(<ResultsDisplay result={GITA} type="text" />);
    expect(screen.getByText('Shloka Overview')).toBeInTheDocument();
    rerender(<ResultsDisplay result={GITA} type="text" compact />);
    expect(screen.queryByText('Shloka Overview')).not.toBeInTheDocument();
  });

  it('closes', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    const { container } = render(<ResultsDisplay result={GITA} type="text" onClose={onClose} />);
    await user.click(container.querySelector('.results-header button') as HTMLElement);
    expect(onClose).toHaveBeenCalled();
  });

  it('explains a failed analysis', () => {
    render(<ResultsDisplay result={{ success: false, error: 'Engine offline' }} type="text" />);
    expect(screen.getByText('Engine offline')).toBeInTheDocument();
  });

  it('asks for Sanskrit when every line was rejected', () => {
    const invalid = { success: true, result: { line: [{ line: 'hello', result: { is_valid_input: false } }], verse: [] } };
    render(<ResultsDisplay result={invalid as unknown as IdentifyResponse} type="text" onClose={() => {}} />);
    expect(screen.getByText('Invalid Input')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Try Again' })).toBeInTheDocument();
  });

  it('says when nothing was identified', () => {
    render(<ResultsDisplay result={{ success: true, result: { line: [], verse: [] } }} type="text" />);
    expect(screen.getByText('No meters identified in the provided text.')).toBeInTheDocument();
  });

  it('shows the OCR text for image results', () => {
    render(<ResultsDisplay result={{ ...GITA, ocr_text: 'पठितः पाठः' }} type="image" />);
    expect(screen.getByText('Extracted Text')).toBeInTheDocument();
  });
});
