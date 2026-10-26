/**
 * Inline styles for the datasets page frame, the filter bar and the dataset cards.
 */

export const layoutStyles = {
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
};
