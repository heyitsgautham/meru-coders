import { useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';
import type { DatasetInfo, DatasetRow } from '../types/api';

/**
 * State for the datasets page: the dataset list, the approved community contributions,
 * the dataset being browsed with its current page of rows, and the source and chandas filters.
 */
export function useDatasetBrowser() {
  // State
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // User contributions state
  const [userContributions, setUserContributions] = useState<any[]>([]);
  const [contributionsLoading, setContributionsLoading] = useState(false);
  const [showContributions, setShowContributions] = useState(false);

  const [selectedDataset, setSelectedDataset] = useState<DatasetInfo | null>(null);
  const [datasetRows, setDatasetRows] = useState<DatasetRow[]>([]);
  const [datasetLoading, setDatasetLoading] = useState(false);
  const [datasetError, setDatasetError] = useState<string | null>(null);

  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const limit = 20;

  const [sourceFilter, setSourceFilter] = useState<string>('');
  const [chandasFilter, setChandasFilter] = useState<string>('');
  const [chandasSearch, setChandasSearch] = useState<string>('');

  // Load datasets
  useEffect(() => {
    async function loadDatasets() {
      try {
        setLoading(true);
        const response = await api.getDatasets();
        if (response.success && response.datasets) {
          setDatasets(response.datasets);
          setSources(response.sources || []);
        } else {
          setError(response.error || 'Failed to load datasets');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load datasets');
      } finally {
        setLoading(false);
      }
    }
    loadDatasets();
  }, []);

  // Load user contributions
  useEffect(() => {
    async function loadContributions() {
      try {
        setContributionsLoading(true);
        const response = await api.getApprovedContributions({ limit: 100, type: 'verse' });
        if (response.success && response.contributions) {
          setUserContributions(response.contributions);
        }
      } catch (err) {
        console.error('Failed to load contributions:', err);
      } finally {
        setContributionsLoading(false);
      }
    }
    loadContributions();
  }, []);

  // Load dataset contents
  const loadDatasetContents = useCallback(async (datasetId: string, page: number = 1, chandas?: string) => {
    try {
      setDatasetLoading(true);
      setDatasetError(null);
      const offset = (page - 1) * limit;

      const response = await api.getDataset(datasetId, {
        limit,
        offset,
        chandas: chandas || undefined
      });

      if (response.success && response.rows) {
        setDatasetRows(response.rows);
        setTotalCount(response.totalCount || 0);
        setCurrentPage(page);
      } else {
        setDatasetError(response.error || 'Failed to load dataset');
      }
    } catch (err) {
      setDatasetError(err instanceof Error ? err.message : 'Failed to load dataset');
    } finally {
      setDatasetLoading(false);
    }
  }, [limit]);

  // Handlers
  const handleSelectDataset = useCallback((dataset: DatasetInfo) => {
    setSelectedDataset(dataset);
    setShowContributions(false);
    setChandasFilter('');
    setChandasSearch('');
    setCurrentPage(1);
    loadDatasetContents(dataset.id, 1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [loadDatasetContents]);

  const handleSelectContributions = useCallback(() => {
    setShowContributions(true);
    setSelectedDataset(null);
    setCurrentPage(1);
    setTotalCount(userContributions.length);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [userContributions.length]);

  const handleCloseDataset = useCallback(() => {
    setSelectedDataset(null);
    setShowContributions(false);
    setDatasetRows([]);
    setChandasFilter('');
    setChandasSearch('');
  }, []);

  const handlePageChange = useCallback((page: number) => {
    if (selectedDataset) {
      loadDatasetContents(selectedDataset.id, page, chandasFilter);
      window.scrollTo({ top: 200, behavior: 'smooth' });
    }
  }, [selectedDataset, chandasFilter, loadDatasetContents]);

  const handleChandasFilter = useCallback((chandas: string) => {
    setChandasFilter(chandas);
    setChandasSearch('');
    setCurrentPage(1);
    if (selectedDataset) {
      loadDatasetContents(selectedDataset.id, 1, chandas);
    }
  }, [selectedDataset, loadDatasetContents]);

  const clearChandasFilter = useCallback(() => {
    setChandasFilter('');
    setChandasSearch('');
    setCurrentPage(1);
    if (selectedDataset) {
      loadDatasetContents(selectedDataset.id, 1);
    }
  }, [selectedDataset, loadDatasetContents]);

  // Filtered data
  const filteredDatasets = sourceFilter
    ? datasets.filter(d => d.source === sourceFilter)
    : datasets;

  const totalPages = Math.ceil(totalCount / limit);

  return {
    datasets,
    sources,
    loading,
    error,
    userContributions,
    contributionsLoading,
    showContributions,
    selectedDataset,
    datasetRows,
    datasetLoading,
    datasetError,
    totalCount,
    currentPage,
    setCurrentPage,
    limit,
    sourceFilter,
    setSourceFilter,
    chandasFilter,
    chandasSearch,
    setChandasSearch,
    handleSelectDataset,
    handleSelectContributions,
    handleCloseDataset,
    handlePageChange,
    handleChandasFilter,
    clearChandasFilter,
    filteredDatasets,
    totalPages,
  };
}

export type DatasetBrowser = ReturnType<typeof useDatasetBrowser>;
