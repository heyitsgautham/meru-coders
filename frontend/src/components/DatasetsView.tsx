/**
 * DatasetsView Component
 * A beautifully designed page for browsing Sanskrit verse datasets
 */

import { Loader2, X } from 'lucide-react';
import { SlokaChecker } from './SlokaChecker';
import { styles } from './datasets/datasetsStyles';
import { ContributionsTable } from './datasets/ContributionsTable';
import { DatasetDetail } from './datasets/DatasetDetail';
import { DatasetFilterBar } from './datasets/DatasetFilterBar';
import { DatasetGrid } from './datasets/DatasetGrid';
import { useDatasetBrowser } from '../hooks/useDatasetBrowser';


/* ============================================================================
   Main Component
   ============================================================================ */

export function DatasetsView() {
  const browser = useDatasetBrowser();
  const { loading, error, selectedDataset, showContributions } = browser;

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
        <DatasetFilterBar browser={browser} />

        {/* Dataset Cards or Detail View */}
        {!selectedDataset && !showContributions ? (
          <DatasetGrid browser={browser} />
        ) : showContributions ? (
          <ContributionsTable browser={browser} />
        ) : selectedDataset ? (
          <DatasetDetail browser={browser} />
        ) : null}
      </div>

      {/* Keyframes for spinner */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
