import { Search, X } from 'lucide-react';
import type { DatasetBrowser } from '../../hooks/useDatasetBrowser';
import { styles } from './datasetsStyles';

/** Source filter, plus the chandas search while a dataset is open. */
export function DatasetFilterBar({ browser }: { browser: DatasetBrowser }) {
  const { sources, selectedDataset, sourceFilter, setSourceFilter, chandasFilter, chandasSearch, setChandasSearch, handleChandasFilter, clearChandasFilter } = browser;
  return (
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
              data-leading-icon
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
  );
}
