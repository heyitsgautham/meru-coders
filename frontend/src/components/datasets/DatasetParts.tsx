/**
 * Presentational pieces of DatasetsView: dataset cards, pagination and table rows.
 */

import { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { DatasetInfo, DatasetRow } from '../../types/api';
import { styles } from './datasetsStyles';

/* ============================================================================
   Components
   ============================================================================ */

// Dataset Card
export function DatasetCard({ 
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
export function Pagination({
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
export function getPatternColumnHeader(patternType?: string): string {
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
export function getPatternTagStyle(patternType?: string): React.CSSProperties {
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
export function TableRow({ 
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
