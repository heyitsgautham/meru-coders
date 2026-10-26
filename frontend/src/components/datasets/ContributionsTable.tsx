import { ArrowLeft, Loader2 } from 'lucide-react';
import { Pagination } from './DatasetParts';
import type { DatasetBrowser } from '../../hooks/useDatasetBrowser';
import { styles } from './datasetsStyles';

/** Approved community contributions, paged in the browser. */
export function ContributionsTable({ browser }: { browser: DatasetBrowser }) {
  const { userContributions, contributionsLoading, currentPage, setCurrentPage, limit, handleCloseDataset } = browser;
  return (
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
  );
}
