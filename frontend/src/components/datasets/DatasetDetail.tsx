import { ArrowLeft, Loader2 } from 'lucide-react';
import AtharvaVedaImg from '../../assets/Atharva_Veda.png';
import { Pagination, TableRow, getPatternColumnHeader } from './DatasetParts';
import type { DatasetBrowser } from '../../hooks/useDatasetBrowser';
import { styles } from './datasetsStyles';

/** The open dataset: its header, one page of rows and the pager. */
export function DatasetDetail({ browser }: { browser: DatasetBrowser }) {
  const { selectedDataset, datasetRows, datasetLoading, datasetError, totalCount, currentPage, limit, chandasFilter, handleCloseDataset, handlePageChange, totalPages } = browser;
  if (!selectedDataset) return null;
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
  );
}
