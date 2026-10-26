import { Loader2, Search } from 'lucide-react';
import { DatasetCard } from './DatasetParts';
import type { DatasetBrowser } from '../../hooks/useDatasetBrowser';
import { styles } from './datasetsStyles';

/** One card per dataset, plus the community contributions card. */
export function DatasetGrid({ browser }: { browser: DatasetBrowser }) {
  const { userContributions, contributionsLoading, sourceFilter, handleSelectDataset, handleSelectContributions, filteredDatasets } = browser;
  return (
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
  );
}
