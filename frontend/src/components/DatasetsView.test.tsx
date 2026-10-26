import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as api from '../services/api';
import { DatasetsView } from './DatasetsView';

vi.mock('../services/api', () => ({
  getDatasets: vi.fn(),
  getDataset: vi.fn(),
  getApprovedContributions: vi.fn(),
  validateSloka: vi.fn(),
  searchSloka: vi.fn(),
}));

const mocked = vi.mocked(api);

const RIGVEDA = {
  id: 'rigveda',
  name: 'Rigveda with Meters',
  description: 'Complete Rigveda verses',
  source: 'GRETIL / Vedaweb',
  sourceReference: '',
  rowCount: 45,
  dataType: 'verses',
  hasSloka: true,
  slokaColumn: 'verse_text',
  chandasColumn: 'meter',
  patternColumn: null,
  patternType: 'lg_pattern',
  isMerged: false,
  uniqueChandas: ['gāyatrī', 'triṣṭup'],
};
const IITK = { ...RIGVEDA, id: 'iitk', name: 'IITK Meter Definitions', source: 'IIT Kanpur', rowCount: 3, uniqueChandas: [] };

function rows(n: number) {
  return Array.from({ length: n }, (_, i) => ({ sloka: `verse ${i}`, chandas: 'gāyatrī', source: 'RV' }));
}

beforeEach(() => {
  vi.resetAllMocks();
  window.scrollTo = vi.fn();
  mocked.getDatasets.mockResolvedValue({ success: true, datasets: [RIGVEDA, IITK], sources: ['GRETIL / Vedaweb', 'IIT Kanpur'] } as never);
  mocked.getApprovedContributions.mockResolvedValue({ success: true, contributions: [], count: 0 } as never);
  mocked.getDataset.mockResolvedValue({ success: true, rows: rows(20), totalCount: 45 } as never);
});

async function openRigveda() {
  const user = userEvent.setup();
  render(<DatasetsView />);
  await user.click(await screen.findByText('Rigveda with Meters'));
  await screen.findByText('verse 0');
  return user;
}

describe('DatasetsView', () => {
  it('lists every dataset with the sloka checker above', async () => {
    render(<DatasetsView />);
    expect(await screen.findByText('IITK Meter Definitions')).toBeInTheDocument();
    expect(screen.getByText('Sloka Checker')).toBeInTheDocument();
  });

  it('filters the cards by source', async () => {
    const user = userEvent.setup();
    render(<DatasetsView />);
    await screen.findByText('Rigveda with Meters');
    await user.selectOptions(screen.getByRole('combobox'), 'IIT Kanpur');
    expect(screen.queryByText('Rigveda with Meters')).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Clear' }));
    expect(screen.getByText('Rigveda with Meters')).toBeInTheDocument();
  });

  it('opens a dataset on its first page and pages through it', async () => {
    const user = await openRigveda();
    expect(mocked.getDataset).toHaveBeenLastCalledWith('rigveda', { limit: 20, offset: 0, chandas: undefined });
    await user.click(screen.getByRole('button', { name: /Next/ }));
    await waitFor(() => expect(mocked.getDataset).toHaveBeenLastCalledWith('rigveda', { limit: 20, offset: 20, chandas: undefined }));
  });

  it('filters rows by a chandas typed exactly', async () => {
    const user = await openRigveda();
    await user.type(screen.getByPlaceholderText('Search chandas...'), 'gāyatrī');
    await waitFor(() => expect(mocked.getDataset).toHaveBeenLastCalledWith('rigveda', { limit: 20, offset: 0, chandas: 'gāyatrī' }));
  });

  it('goes back to the cards', async () => {
    const user = await openRigveda();
    await user.click(screen.getByRole('button', { name: /Back to datasets/ }));
    expect(screen.getByText('IITK Meter Definitions')).toBeInTheDocument();
  });

  it('says when a dataset fails to load', async () => {
    mocked.getDataset.mockResolvedValue({ success: false, error: 'Dataset not found' } as never);
    const user = userEvent.setup();
    render(<DatasetsView />);
    await user.click(await screen.findByText('Rigveda with Meters'));
    expect(await screen.findByText('Dataset not found')).toBeInTheDocument();
  });

  it('shows approved contributions behind their own card', async () => {
    mocked.getApprovedContributions.mockResolvedValue({
      success: true,
      count: 1,
      contributions: [
        { id: 'c1', data: { verse_text: 'अग्निमीळे', meter: 'गायत्री' }, submitted_by: { username: 'kalidasa' }, reviewed_at: '2026-01-02' },
      ],
    } as never);
    const user = userEvent.setup();
    render(<DatasetsView />);
    await user.click(await screen.findByText('🌟 Community Contributions'));
    expect(screen.getByText('अग्निमीळे')).toBeInTheDocument();
    expect(screen.getByText('kalidasa')).toBeInTheDocument();
  });

  it('reports a failure to list datasets', async () => {
    mocked.getDatasets.mockRejectedValue(new Error('offline'));
    render(<DatasetsView />);
    expect(await screen.findByText('Unable to Load Datasets')).toBeInTheDocument();
  });
});
