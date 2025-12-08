/**
 * DatasetsView Component
 * A beautifully designed page for browsing Sanskrit verse datasets
 */

import { useState, useEffect, useCallback } from 'react';
import { Loader2, ChevronLeft, ChevronRight, Search, X, ArrowLeft } from 'lucide-react';
import * as api from '../services/api';
import type { DatasetInfo, DatasetRow } from '../types/api';
import { SlokaChecker } from './SlokaChecker';

// Import Atharvaveda book cover for special dataset header
import AtharvaVedaImg from '../assets/Atharva_Veda.png';

/* ============================================================================
   Custom Styles - Embedded for this component
   ============================================================================ */

const styles = {
  // Page container
  page: {
    minHeight: '100vh',
    background: '#FFF6EA',
    paddingBottom: '80px',
  } as React.CSSProperties,

  // Page header
  pageHeader: {
    textAlign: 'center' as const,
    padding: '48px 24px 56px',
    maxWidth: '720px',
    margin: '0 auto',
  },
  pageTitle: {
    fontSize: '2.25rem',
    fontWeight: 700,
    color: '#78350f',
    marginBottom: '16px',
    letterSpacing: '-0.02em',
    lineHeight: 1.2,
  },
  pageSubtitle: {
    fontSize: '1.125rem',
    color: '#92400e',
    lineHeight: 1.7,
    fontWeight: 400,
  },

  // Main content wrapper
  contentWrapper: {
    maxWidth: '1280px',
    margin: '0 auto',
    padding: '0 32px',
  },

  // Source filter bar
  filterBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '16px',
    padding: '20px 24px',
    background: '#FFFAF4',
    borderRadius: '16px',
    marginBottom: '32px',
    boxShadow: '0 1px 4px rgba(0, 0, 0, 0.03)',
    border: '1px solid #f0e6da',
  },
  filterBarLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  filterBarRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  filterLabel: {
    fontSize: '0.875rem',
    fontWeight: 600,
    color: '#92400e',
  },
  filterSelect: {
    padding: '10px 16px',
    paddingRight: '40px',
    fontSize: '0.875rem',
    color: '#78350f',
    background: '#FFFAF4',
    border: '1px solid #e8ddd0',
    borderRadius: '10px',
    cursor: 'pointer',
    outline: 'none',
    minWidth: '220px',
    appearance: 'none' as const,
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23b45309' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    transition: 'border-color 0.2s, box-shadow 0.2s',
  },
  filterClear: {
    fontSize: '0.875rem',
    color: '#d97706',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 12px',
    borderRadius: '8px',
    transition: 'color 0.2s, background 0.2s',
  },
  // Chandas search in filter bar
  chandasSearchInline: {
    position: 'relative' as const,
    width: '240px',
  },
  chandasSearchIconInline: {
    position: 'absolute' as const,
    left: '12px',
    top: '50%',
    transform: 'translateY(-50%)',
    color: '#b45309',
    pointerEvents: 'none' as const,
  },
  chandasSearchInputInline: {
    width: '100%',
    padding: '10px 14px 10px 38px',
    fontSize: '0.875rem',
    background: '#FFFAF4',
    border: '1px solid #e8ddd0',
    borderRadius: '10px',
    outline: 'none',
    color: '#78350f',
    transition: 'border-color 0.2s, box-shadow 0.2s',
  },
  chandasFilterBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
    color: '#fff',
    padding: '6px 12px',
    borderRadius: '20px',
    fontSize: '0.8rem',
    fontWeight: 500,
    boxShadow: '0 2px 6px rgba(217, 119, 6, 0.25)',
  },

  // Dataset cards grid
  cardsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
    gap: '24px',
    marginBottom: '40px',
  },

  // Individual dataset card
  card: {
    background: '#FFFAF4',
    borderRadius: '20px',
    padding: '28px',
    cursor: 'pointer',
    border: '1px solid #f0e6da',
    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
    position: 'relative' as const,
  },
  cardHover: {
    transform: 'translateY(-4px)',
    boxShadow: '0 12px 28px -8px rgba(0, 0, 0, 0.08)',
    borderColor: '#e8ddd0',
  },
  cardTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#78350f',
    marginBottom: '10px',
    lineHeight: 1.4,
    fontFamily: "'Noto Sans Devanagari', sans-serif",
  },
  cardDescription: {
    fontSize: '0.9rem',
    color: '#92400e',
    lineHeight: 1.65,
    marginBottom: '20px',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical' as const,
    overflow: 'hidden',
  },
  cardMeta: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: '16px',
    borderTop: '1px solid #f0e6da',
  },
  cardSource: {
    fontSize: '0.8rem',
    color: '#b45309',
    maxWidth: '180px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  cardCount: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#92400e',
    background: '#f5ead8',
    padding: '6px 12px',
    borderRadius: '20px',
  },
  cardBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '0.75rem',
    fontWeight: 600,
    marginTop: '16px',
    padding: '4px 10px',
    borderRadius: '12px',
    background: 'rgba(254, 243, 199, 0.6)',
  },
  badgeDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
  },

  // Back button
  backButton: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '0.9rem',
    color: '#92400e',
    background: '#f5ead8',
    border: '1px solid #e8ddd0',
    cursor: 'pointer',
    padding: '10px 18px',
    marginBottom: '24px',
    borderRadius: '12px',
    transition: 'all 0.2s',
  },

  // Dataset detail header
  detailHeader: {
    background: 'linear-gradient(135deg, #fef7ed 0%, #fdf4e7 50%, #fcf0dd 100%)',
    borderRadius: '24px',
    padding: '36px 40px',
    marginBottom: '28px',
    border: '1px solid #f5e6d3',
  },
  // Atharvaveda special header with book cover
  atharvavedaHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '40px',
    background: 'linear-gradient(135deg, #fff7ed 0%, #ffedd5 50%, #fed7aa 100%)',
    borderRadius: '24px',
    padding: '40px',
    marginBottom: '28px',
    border: '1px solid #fdba74',
    boxShadow: '0 8px 32px rgba(251, 146, 60, 0.15)',
    overflow: 'hidden',
    position: 'relative' as const,
  },
  atharvavedaBookCover: {
    width: '140px',
    height: '200px',
    borderRadius: '12px',
    objectFit: 'cover' as const,
    boxShadow: '0 8px 24px rgba(194, 65, 12, 0.25)',
    flexShrink: 0,
    border: '3px solid #fff',
  },
  atharvavedaContent: {
    flex: 1,
    minWidth: 0,
  },
  atharvavedaTitle: {
    fontSize: '2rem',
    fontWeight: 700,
    color: '#9a3412',
    marginBottom: '8px',
    fontFamily: "'Noto Sans Devanagari', sans-serif",
    letterSpacing: '-0.01em',
  },
  atharvavedaSanskritTitle: {
    fontSize: '1.5rem',
    fontWeight: 500,
    color: '#c2410c',
    marginBottom: '16px',
    fontFamily: "'Noto Sans Devanagari', sans-serif",
  },
  atharvavedaDescription: {
    fontSize: '1rem',
    color: '#78350f',
    lineHeight: 1.7,
    marginBottom: '20px',
    maxWidth: '700px',
  },
  atharvavedaMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
    fontSize: '0.875rem',
    color: '#92400e',
  },
  atharvavedaMetaItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    background: 'rgba(251, 146, 60, 0.2)',
    padding: '8px 16px',
    borderRadius: '8px',
    border: '1px solid rgba(251, 146, 60, 0.3)',
  },
  atharvavedaGlow: {
    position: 'absolute' as const,
    top: '-50%',
    right: '-10%',
    width: '400px',
    height: '400px',
    background: 'radial-gradient(circle, rgba(251, 146, 60, 0.2) 0%, transparent 70%)',
    pointerEvents: 'none' as const,
  },
  detailTitle: {
    fontSize: '1.75rem',
    fontWeight: 700,
    color: '#1a1a1a',
    marginBottom: '12px',
    fontFamily: "'Noto Sans Devanagari', sans-serif",
    letterSpacing: '-0.01em',
  },
  detailDescription: {
    fontSize: '1rem',
    color: '#555',
    lineHeight: 1.7,
    marginBottom: '20px',
    maxWidth: '800px',
  },
  detailMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
    fontSize: '0.875rem',
    color: '#777',
  },
  detailMetaItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },

  // Data table container
  tableContainer: {
    background: '#FFFAF4',
    borderRadius: '20px',
    overflow: 'hidden',
    border: '1px solid #f0e6da',
    boxShadow: '0 1px 4px rgba(0, 0, 0, 0.03)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
  },
  tableHeader: {
    background: '#f5ead8',
  },
  tableHeaderCell: {
    padding: '16px 24px',
    fontSize: '0.75rem',
    fontWeight: 700,
    color: '#92400e',
    textAlign: 'left' as const,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
    borderBottom: '1px solid #e8ddd0',
  },
  tableRow: {
    transition: 'background 0.15s',
  },
  tableRowHover: {
    background: 'rgba(245, 234, 216, 0.4)',
  },
  tableCell: {
    padding: '20px 24px',
    fontSize: '0.9rem',
    color: '#78350f',
    borderBottom: '1px solid #f0e6da',
    verticalAlign: 'top' as const,
  },
  tableCellNumber: {
    color: '#b45309',
    fontWeight: 600,
    width: '60px',
  },
  chandasTag: {
    display: 'inline-block',
    padding: '6px 14px',
    background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
    color: '#fff',
    borderRadius: '8px',
    fontSize: '0.85rem',
    fontWeight: 600,
    fontFamily: "'Noto Sans Devanagari', sans-serif",
    boxShadow: '0 2px 6px rgba(217, 119, 6, 0.25)',
  },
  patternTag: {
    display: 'inline-block',
    padding: '6px 14px',
    background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
    color: '#fff',
    borderRadius: '8px',
    fontSize: '0.85rem',
    fontWeight: 500,
    fontFamily: "'Noto Sans Devanagari', monospace",
    letterSpacing: '0.03em',
    boxShadow: '0 2px 6px rgba(124, 58, 237, 0.25)',
  },
  syllableCountTag: {
    display: 'inline-block',
    padding: '6px 14px',
    background: 'linear-gradient(135deg, #0891b2 0%, #0e7490 100%)',
    color: '#fff',
    borderRadius: '8px',
    fontSize: '0.95rem',
    fontWeight: 600,
    fontFamily: "'Noto Sans Devanagari', sans-serif",
    boxShadow: '0 2px 6px rgba(8, 145, 178, 0.25)',
  },
  matraCountTag: {
    display: 'inline-block',
    padding: '6px 14px',
    background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
    color: '#fff',
    borderRadius: '8px',
    fontSize: '0.85rem',
    fontWeight: 500,
    fontFamily: "'Noto Sans Devanagari', monospace",
    letterSpacing: '0.05em',
    boxShadow: '0 2px 6px rgba(5, 150, 105, 0.25)',
  },
  categoryTag: {
    display: 'inline-block',
    padding: '4px 10px',
    background: '#f0e6da',
    color: '#92400e',
    borderRadius: '6px',
    fontSize: '0.75rem',
    fontWeight: 500,
    marginLeft: '8px',
  },
  slokaText: {
    fontFamily: "'Noto Sans Devanagari', sans-serif",
    fontSize: '1rem',
    lineHeight: 2,
    color: '#78350f',
    whiteSpace: 'pre-wrap' as const,
    maxWidth: '600px',
  },
  sourceText: {
    color: '#b45309',
    fontSize: '0.85rem',
  },

  // Pagination
  pagination: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 24px',
    borderTop: '1px solid #e8ddd0',
    background: '#f5ead8',
  },
  paginationInfo: {
    fontSize: '0.875rem',
    color: '#92400e',
  },
  paginationControls: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  paginationButton: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 16px',
    fontSize: '0.875rem',
    color: '#92400e',
    background: '#FFFAF4',
    border: '1px solid #e8ddd0',
    borderRadius: '10px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  paginationButtonDisabled: {
    opacity: 0.4,
    cursor: 'not-allowed',
  },
  paginationPage: {
    fontSize: '0.875rem',
    color: '#78350f',
    minWidth: '120px',
    textAlign: 'center' as const,
  },

  // Loading state
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '100px 20px',
  },
  loadingText: {
    fontSize: '1.125rem',
    color: '#92400e',
    marginTop: '20px',
  },

  // Empty state
  emptyState: {
    textAlign: 'center' as const,
    padding: '80px 20px',
  },
  emptyIcon: {
    width: '80px',
    height: '80px',
    background: '#f5ead8',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
  },
  emptyTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#78350f',
    marginBottom: '8px',
  },
  emptyText: {
    fontSize: '1rem',
    color: '#b45309',
  },
};

/* ============================================================================
   Components
   ============================================================================ */

// Dataset Card
function DatasetCard({ 
  dataset, 
  onClick 
}: { 
  dataset: DatasetInfo; 
  onClick: () => void;
}) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        ...styles.card,
        ...(isHovered ? styles.cardHover : {}),
      }}
    >
      <h3 style={styles.cardTitle}>{dataset.name}</h3>
      <p style={styles.cardDescription}>{dataset.description}</p>
      
      <div style={styles.cardMeta}>
        <span style={styles.cardSource}>{dataset.source}</span>
        <span style={styles.cardCount}>
          {dataset.rowCount.toLocaleString()} entries
        </span>
      </div>
      
      {dataset.hasSloka ? (
        <div style={{ ...styles.cardBadge, color: '#047857', background: 'rgba(167, 243, 208, 0.5)' }}>
          <span style={{ ...styles.badgeDot, background: '#10b981' }}></span>
          Contains verses
        </div>
      ) : dataset.dataType === 'meter_definitions' ? (
        <div style={{ ...styles.cardBadge, color: '#7c3aed', background: 'rgba(221, 214, 254, 0.5)' }}>
          <span style={{ ...styles.badgeDot, background: '#8b5cf6' }}></span>
          Meter definitions
        </div>
      ) : null}
    </div>
  );
}

// Pagination Component
function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  totalCount,
  limit,
  offset
}: {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  totalCount: number;
  limit: number;
  offset: number;
}) {
  const startItem = offset + 1;
  const endItem = Math.min(offset + limit, totalCount);

  return (
    <div style={styles.pagination}>
      <span style={styles.paginationInfo}>
        Showing <strong>{startItem.toLocaleString()}</strong> – <strong>{endItem.toLocaleString()}</strong> of {totalCount.toLocaleString()}
      </span>
      <div style={styles.paginationControls}>
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          style={{
            ...styles.paginationButton,
            ...(currentPage === 1 ? styles.paginationButtonDisabled : {}),
          }}
        >
          <ChevronLeft size={16} />
          Previous
        </button>
        <span style={styles.paginationPage}>
          Page <strong>{currentPage}</strong> of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          style={{
            ...styles.paginationButton,
            ...(currentPage === totalPages ? styles.paginationButtonDisabled : {}),
          }}
        >
          Next
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

// Helper function to get pattern column header based on type
function getPatternColumnHeader(patternType?: string): string {
  switch (patternType) {
    case 'syllable_count':
      return 'Syllable Count';
    case 'matra_count':
      return 'Matra Pattern';
    case 'lg_pattern':
    default:
      return 'L-G Pattern';
  }
}

// Helper function to get pattern tag style based on type
function getPatternTagStyle(patternType?: string): React.CSSProperties {
  switch (patternType) {
    case 'syllable_count':
      return styles.syllableCountTag;
    case 'matra_count':
      return styles.matraCountTag;
    case 'lg_pattern':
    default:
      return styles.patternTag;
  }
}

// Table Row with hover state
function TableRow({ 
  row, 
  index, 
  currentPage, 
  limit, 
  selectedDataset 
}: { 
  row: DatasetRow; 
  index: number; 
  currentPage: number; 
  limit: number;
  selectedDataset: DatasetInfo;
}) {
  const [isHovered, setIsHovered] = useState(false);
  const patternType = selectedDataset.patternType;

  return (
    <tr
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        ...styles.tableRow,
        ...(isHovered ? styles.tableRowHover : {}),
      }}
    >
      <td style={{ ...styles.tableCell, ...styles.tableCellNumber }}>
        {(currentPage - 1) * limit + index + 1}
      </td>
      <td style={styles.tableCell}>
        <span style={styles.chandasTag}>
          {row.chandas || '—'}
        </span>
        {row.category && (
          <span style={styles.categoryTag}>
            {row.category}
          </span>
        )}
      </td>
      {selectedDataset.hasSloka ? (
        <td style={styles.tableCell}>
          <div style={styles.slokaText}>
            {row.sloka || '—'}
          </div>
        </td>
      ) : selectedDataset.patternColumn ? (
        <td style={styles.tableCell}>
          <span style={getPatternTagStyle(patternType)}>
            {row.pattern || '—'}
          </span>
        </td>
      ) : null}
      <td style={{ ...styles.tableCell, ...styles.sourceText }}>
        {row.source}
      </td>
    </tr>
  );
}

/* ============================================================================
   Main Component
   ============================================================================ */

export function DatasetsView() {
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

  // Loading state
  if (loading) {
    return (
      <div style={styles.page}>
        <div style={styles.loadingContainer}>
          <Loader2 size={40} color="#d97706" style={{ animation: 'spin 1s linear infinite' }} />
          <p style={styles.loadingText}>Loading datasets...</p>
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={styles.page}>
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>
            <X size={32} color="#999" />
          </div>
          <h3 style={styles.emptyTitle}>Unable to Load Datasets</h3>
          <p style={styles.emptyText}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      {/* Header */}
      <div style={styles.pageHeader}>
        <h1 style={styles.pageTitle}>Sanskrit Verse Datasets</h1>
        <p style={styles.pageSubtitle}>
          Explore curated collections of Sanskrit verses and meter definitions. 
          Each dataset contains carefully annotated entries with their identified chandas.
        </p>
      </div>

      <div style={styles.contentWrapper}>
        {/* Sloka Checker - Only show on main datasets page, not when viewing a specific dataset */}
        {!selectedDataset && !showContributions && (
          <SlokaChecker />
        )}

        {/* Filter Bar */}
        <div style={styles.filterBar}>
          <div style={styles.filterBarLeft}>
            <span style={styles.filterLabel}>Filter by source:</span>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              style={styles.filterSelect}
            >
              <option value="">All Sources</option>
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
            {sourceFilter && (
              <button
                onClick={() => setSourceFilter('')}
                style={styles.filterClear}
                onMouseEnter={(e) => e.currentTarget.style.color = '#d97706'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#888'}
              >
                <X size={14} />
                Clear
              </button>
            )}
          </div>
          
          {/* Chandas search on right - only show when a dataset is selected */}
          {selectedDataset && selectedDataset.uniqueChandas.length > 0 && (
            <div style={styles.filterBarRight}>
              {chandasFilter && (
                <span style={styles.chandasFilterBadge}>
                  {chandasFilter}
                  <button
                    onClick={clearChandasFilter}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', padding: 0 }}
                  >
                    <X size={12} color="#fff" />
                  </button>
                </span>
              )}
              <div style={styles.chandasSearchInline}>
                <Search size={14} style={styles.chandasSearchIconInline} />
                <input
                  type="text"
                  placeholder="Search chandas..."
                  value={chandasSearch}
                  onChange={(e) => {
                    setChandasSearch(e.target.value);
                    // Auto-filter when user types (debounced effect)
                    const searchTerm = e.target.value.trim();
                    if (searchTerm && selectedDataset.uniqueChandas.some(c => 
                      c.toLowerCase() === searchTerm.toLowerCase()
                    )) {
                      handleChandasFilter(searchTerm);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && chandasSearch.trim()) {
                      // Find exact or first partial match
                      const match = selectedDataset.uniqueChandas.find(c =>
                        c.toLowerCase().includes(chandasSearch.toLowerCase())
                      );
                      if (match) {
                        handleChandasFilter(match);
                        setChandasSearch('');
                      }
                    }
                  }}
                  style={styles.chandasSearchInputInline}
                  onFocus={(e) => {
                    e.currentTarget.style.borderColor = '#d97706';
                    e.currentTarget.style.boxShadow = '0 0 0 3px rgba(217, 119, 6, 0.1)';
                  }}
                  onBlur={(e) => {
                    e.currentTarget.style.borderColor = '#e8ddd0';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Dataset Cards or Detail View */}
        {!selectedDataset && !showContributions ? (
          <>
            {filteredDatasets.length > 0 ? (
              <>
                <div style={styles.cardsGrid}>
                  {filteredDatasets.map(dataset => (
                    <DatasetCard
                      key={dataset.id}
                      dataset={dataset}
                      onClick={() => handleSelectDataset(dataset)}
                    />
                  ))}
                  
                  {/* Community Contributions Card */}
                  {userContributions.length > 0 && !sourceFilter && (
                    <div
                      onClick={handleSelectContributions}
                      style={{
                        ...styles.card,
                        borderLeft: '4px solid #10b981',
                        cursor: 'pointer',
                      }}
                      onMouseEnter={(e) => {
                        Object.assign(e.currentTarget.style, styles.cardHover);
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                        e.currentTarget.style.borderColor = '#10b981';
                      }}
                    >
                      <h3 style={styles.cardTitle}>🌟 Community Contributions</h3>
                      <p style={styles.cardDescription}>
                        User-contributed verses that have been reviewed and approved by our team. 
                        Browse contributions from community members.
                      </p>
                      <div style={styles.cardMeta}>
                        <span style={styles.cardSource}>Community</span>
                        <span style={styles.cardCount}>
                          {userContributions.length} {userContributions.length === 1 ? 'verse' : 'verses'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {contributionsLoading && (
                  <div style={{ textAlign: 'center', padding: '32px', color: '#92400e' }}>
                    <Loader2 size={24} style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }} />
                    <p style={{ marginTop: '8px' }}>Loading contributions...</p>
                  </div>
                )}
              </>
            ) : (
              <div style={styles.emptyState}>
                <div style={styles.emptyIcon}>
                  <Search size={32} color="#999" />
                </div>
                <h3 style={styles.emptyTitle}>No Datasets Found</h3>
                <p style={styles.emptyText}>
                  {sourceFilter ? 'Try selecting a different source' : 'No datasets available'}
                </p>
              </div>
            )}
          </>
        ) : showContributions ? (
          <>
            {/* Back Button */}
            <button
              onClick={handleCloseDataset}
              style={styles.backButton}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#ecddc8';
                e.currentTarget.style.color = '#78350f';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f5ead8';
                e.currentTarget.style.color = '#92400e';
              }}
            >
              <ArrowLeft size={18} />
              Back to datasets
            </button>

            {/* Detail Header */}
            <div style={styles.detailHeader}>
              <h2 style={styles.detailTitle}>🌟 Community Contributions</h2>
              <p style={styles.detailDescription}>
                User-contributed verses that have been reviewed and approved by our team
              </p>
              <div style={styles.detailMeta}>
                <span style={styles.detailMetaItem}>
                  📚 Community Collection
                </span>
                <span style={styles.detailMetaItem}>
                  📊 {userContributions.length.toLocaleString()} entries
                </span>
              </div>
            </div>

            {/* Contributions Table */}
            <div style={styles.tableContainer}>
              {contributionsLoading ? (
                <div style={{ ...styles.loadingContainer, padding: '60px 20px' }}>
                  <Loader2 size={32} color="#d97706" style={{ animation: 'spin 1s linear infinite' }} />
                  <p style={{ ...styles.loadingText, fontSize: '1rem' }}>Loading contributions...</p>
                </div>
              ) : userContributions.length === 0 ? (
                <div style={styles.emptyState}>
                  <p style={styles.emptyText}>No approved contributions yet</p>
                </div>
              ) : (
                <>
                  <table style={styles.table}>
                    <thead style={styles.tableHeader}>
                      <tr>
                        <th style={{ ...styles.tableHeaderCell, width: '60px' }}>#</th>
                        <th style={{ ...styles.tableHeaderCell, width: '180px' }}>Meter</th>
                        <th style={styles.tableHeaderCell}>Verse</th>
                        <th style={{ ...styles.tableHeaderCell, width: '140px' }}>Contributor</th>
                        <th style={{ ...styles.tableHeaderCell, width: '120px' }}>Approved</th>
                      </tr>
                    </thead>
                    <tbody>
                      {userContributions
                        .slice((currentPage - 1) * limit, currentPage * limit)
                        .map((contrib, index) => (
                          <tr
                            key={contrib.id}
                            style={styles.tableRow}
                          >
                            <td style={{ ...styles.tableCell, ...styles.tableCellNumber }}>
                              {(currentPage - 1) * limit + index + 1}
                            </td>
                            <td style={styles.tableCell}>
                              <span style={styles.chandasTag}>
                                {contrib.data?.meter_name || contrib.data?.meter || '—'}
                              </span>
                            </td>
                            <td style={styles.tableCell}>
                              <div style={styles.slokaText}>
                                {contrib.data?.verse_text || '—'}
                              </div>
                            </td>
                            <td style={{ ...styles.tableCell, ...styles.sourceText }}>
                              {contrib.submitted_by?.username || 'Anonymous'}
                            </td>
                            <td style={{ ...styles.tableCell, fontSize: '0.8rem', color: '#92400e' }}>
                              {new Date(contrib.reviewed_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>

                  {Math.ceil(userContributions.length / limit) > 1 && (
                    <Pagination
                      currentPage={currentPage}
                      totalPages={Math.ceil(userContributions.length / limit)}
                      onPageChange={(page) => {
                        setCurrentPage(page);
                        window.scrollTo({ top: 200, behavior: 'smooth' });
                      }}
                      totalCount={userContributions.length}
                      limit={limit}
                      offset={(currentPage - 1) * limit}
                    />
                  )}
                </>
              )}
            </div>
          </>
        ) : selectedDataset ? (
          <>
            {/* Back Button */}
            <button
              onClick={handleCloseDataset}
              style={styles.backButton}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#ecddc8';
                e.currentTarget.style.color = '#78350f';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f5ead8';
                e.currentTarget.style.color = '#92400e';
              }}
            >
              <ArrowLeft size={18} />
              Back to datasets
            </button>

            {/* Detail Header - Special layout for Atharvaveda */}
            {selectedDataset.id === 'atharvaveda' ? (
              <div style={styles.atharvavedaHeader}>
                <div style={styles.atharvavedaGlow}></div>
                <img 
                  src={AtharvaVedaImg} 
                  alt="Atharvaveda" 
                  style={styles.atharvavedaBookCover}
                />
                <div style={styles.atharvavedaContent}>
                  <h2 style={styles.atharvavedaTitle}>{selectedDataset.name}</h2>
                  <p style={styles.atharvavedaSanskritTitle}>अथर्ववेद</p>
                  <p style={styles.atharvavedaDescription}>
                    {selectedDataset.description}
                  </p>
                  <div style={styles.atharvavedaMeta}>
                    <span style={styles.atharvavedaMetaItem}>
                      📚 {selectedDataset.sourceReference || selectedDataset.source}
                    </span>
                    <span style={styles.atharvavedaMetaItem}>
                      📊 {selectedDataset.rowCount.toLocaleString()} verses
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div style={styles.detailHeader}>
                <h2 style={styles.detailTitle}>{selectedDataset.name}</h2>
                <p style={styles.detailDescription}>{selectedDataset.description}</p>
                <div style={styles.detailMeta}>
                  <span style={styles.detailMetaItem}>
                    📚 {selectedDataset.sourceReference || selectedDataset.source}
                  </span>
                  <span style={styles.detailMetaItem}>
                    📊 {selectedDataset.rowCount.toLocaleString()} entries
                  </span>
                </div>
              </div>
            )}

            {/* Data Table */}
            <div style={styles.tableContainer}>
              {datasetLoading ? (
                <div style={{ ...styles.loadingContainer, padding: '60px 20px' }}>
                  <Loader2 size={32} color="#d97706" style={{ animation: 'spin 1s linear infinite' }} />
                  <p style={{ ...styles.loadingText, fontSize: '1rem' }}>Loading entries...</p>
                </div>
              ) : datasetError ? (
                <div style={styles.emptyState}>
                  <p style={styles.emptyText}>{datasetError}</p>
                </div>
              ) : datasetRows.length === 0 ? (
                <div style={styles.emptyState}>
                  <p style={styles.emptyText}>
                    No entries found{chandasFilter ? ` for "${chandasFilter}"` : ''}
                  </p>
                </div>
              ) : (
                <>
                  <table style={styles.table}>
                    <thead style={styles.tableHeader}>
                      <tr>
                        <th style={{ ...styles.tableHeaderCell, width: '60px' }}>#</th>
                        <th style={{ ...styles.tableHeaderCell, width: selectedDataset.isMerged ? '220px' : '160px' }}>
                          {selectedDataset.isMerged ? 'Chandas / Type' : 'Chandas'}
                        </th>
                        {selectedDataset.hasSloka ? (
                          <th style={styles.tableHeaderCell}>Sloka</th>
                        ) : selectedDataset.patternColumn ? (
                          <th style={styles.tableHeaderCell}>{getPatternColumnHeader(selectedDataset.patternType)}</th>
                        ) : null}
                        <th style={{ ...styles.tableHeaderCell, width: '180px' }}>Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {datasetRows.map((row, index) => (
                        <TableRow
                          key={index}
                          row={row}
                          index={index}
                          currentPage={currentPage}
                          limit={limit}
                          selectedDataset={selectedDataset}
                        />
                      ))}
                    </tbody>
                  </table>

                  {totalPages > 1 && (
                    <Pagination
                      currentPage={currentPage}
                      totalPages={totalPages}
                      onPageChange={handlePageChange}
                      totalCount={totalCount}
                      limit={limit}
                      offset={(currentPage - 1) * limit}
                    />
                  )}
                </>
              )}
            </div>
          </>
        ) : null}
      </div>

      {/* Keyframes for spinner */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
