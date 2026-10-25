/**
 * Stylesheet for SlokaChecker, injected through a <style> element.
 * Kept as the same template string the component used to inline.
 */

export const SLOKA_CHECKER_CSS = `
        .sloka-checker {
          background: linear-gradient(145deg, #fffbf5 0%, #fef7ed 100%);
          border-radius: 20px;
          padding: 28px;
          margin-bottom: 32px;
          border: 1px solid #f5e6d3;
          box-shadow: 0 4px 20px rgba(120, 53, 15, 0.06);
        }

        /* Header */
        .checker-header {
          display: flex;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 24px;
        }
        .header-icon {
          width: 52px;
          height: 52px;
          background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%);
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          flex-shrink: 0;
        }
        .header-content h3 {
          margin: 0 0 6px 0;
          font-size: 1.35rem;
          font-weight: 700;
          color: #78350f;
        }
        .header-content .english-title {
          font-weight: 500;
          font-size: 1rem;
          color: #92400e;
        }
        .header-content p {
          margin: 0;
          font-size: 0.9rem;
          color: #a16207;
        }

        /* Input Section */
        .input-section {
          margin-bottom: 8px;
        }
        .textarea-wrapper {
          position: relative;
          margin-bottom: 14px;
        }
        .textarea-wrapper textarea {
          width: 100%;
          min-height: 100px;
          padding: 16px;
          padding-right: 44px;
          font-size: 1.05rem;
          font-family: 'Noto Sans Devanagari', 'Noto Sans', sans-serif;
          color: #78350f;
          background: #fff;
          border: 2px solid #e8ddd0;
          border-radius: 14px;
          outline: none;
          resize: vertical;
          transition: all 0.2s ease;
          line-height: 1.9;
        }
        .textarea-wrapper textarea::placeholder {
          color: #c9b99a;
        }
        .textarea-wrapper.focused textarea {
          border-color: #d97706;
          box-shadow: 0 0 0 4px rgba(217, 119, 6, 0.1);
        }
        .clear-btn {
          position: absolute;
          top: 12px;
          right: 12px;
          width: 32px;
          height: 32px;
          border: none;
          background: #f5ead8;
          color: #92400e;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s;
        }
        .clear-btn:hover {
          background: #e8ddd0;
        }

        /* Action Row */
        .action-row {
          display: flex;
          align-items: center;
          gap: 16px;
        }
        .check-btn {
          display: inline-flex;
          align-items: center;
          gap: 10px;
          padding: 14px 28px;
          font-size: 1rem;
          font-weight: 600;
          color: #fff;
          background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
          border: none;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 4px 12px rgba(217, 119, 6, 0.3);
        }
        .check-btn:hover:not(.disabled) {
          transform: translateY(-1px);
          box-shadow: 0 6px 16px rgba(217, 119, 6, 0.4);
        }
        .check-btn.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .hint {
          font-size: 0.8rem;
          color: #a16207;
        }
        .hint kbd {
          display: inline-block;
          padding: 2px 6px;
          font-size: 0.75rem;
          font-family: monospace;
          background: #f5ead8;
          border: 1px solid #e8ddd0;
          border-radius: 4px;
          margin: 0 2px;
        }

        /* Error Box */
        .error-box {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 14px 18px;
          background: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 12px;
          color: #dc2626;
          margin-top: 16px;
          font-size: 0.9rem;
        }

        /* Results Section */
        .results-section {
          margin-top: 24px;
          animation: fadeIn 0.3s ease;
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* Status Banner */
        .status-banner {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 18px 22px;
          border-radius: 14px;
          margin-bottom: 16px;
        }
        .status-banner.success {
          background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
          border: 1px solid #a7f3d0;
        }
        .status-banner.warning {
          background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
          border: 1px solid #fde68a;
        }
        .status-left {
          display: flex;
          align-items: center;
          gap: 14px;
        }
        .status-banner.success .status-left { color: #047857; }
        .status-banner.warning .status-left { color: #b45309; }
        .status-text {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        .status-text strong {
          font-size: 1.05rem;
        }
        .status-text span {
          font-size: 0.8rem;
          opacity: 0.8;
        }
        .similarity-badge {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 10px 18px;
          background: white;
          border-radius: 12px;
          border: 2px solid;
        }
        .similarity-value {
          font-size: 1.3rem;
          font-weight: 700;
        }
        .similarity-label {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #78350f;
        }

        /* Metadata Pills */
        .metadata-row {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
          margin-bottom: 20px;
          align-items: center;
        }
        .meta-pill {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: #fff;
          border: 1px solid #e8ddd0;
          border-radius: 20px;
        }
        .meta-label {
          font-size: 0.7rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #92400e;
        }
        .meta-value {
          font-size: 0.85rem;
          font-weight: 600;
          color: #78350f;
          font-family: 'Noto Sans Devanagari', sans-serif;
        }

        /* Diff Toggle Button */
        .diff-toggle-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          font-size: 0.8rem;
          font-weight: 600;
          color: #7c3aed;
          background: #f5f3ff;
          border: 1px solid #ddd6fe;
          border-radius: 20px;
          cursor: pointer;
          transition: all 0.2s;
          margin-left: auto;
        }
        .diff-toggle-btn:hover {
          background: #ede9fe;
          border-color: #c4b5fd;
        }
        .diff-toggle-btn.active {
          background: #7c3aed;
          color: white;
          border-color: #7c3aed;
        }

        /* Diff View Container */
        .diff-view-container {
          background: #fefce8;
          border: 2px solid #fde047;
          border-radius: 16px;
          overflow: hidden;
          margin-bottom: 20px;
          animation: slideDown 0.3s ease;
        }
        @keyframes slideDown {
          from { opacity: 0; max-height: 0; }
          to { opacity: 1; max-height: 500px; }
        }
        .diff-view-header {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 14px 20px;
          background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%);
          border-bottom: 1px solid #fde047;
          font-weight: 600;
          color: #854d0e;
          font-size: 0.9rem;
        }
        .diff-legend {
          display: flex;
          gap: 16px;
          margin-left: auto;
          font-size: 0.75rem;
          font-weight: 500;
        }
        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .legend-item .legend-color {
          width: 14px;
          height: 14px;
          border-radius: 4px;
        }
        .legend-item.delete .legend-color {
          background: #fecaca;
          border: 1px solid #f87171;
        }
        .legend-item.insert .legend-color {
          background: #bbf7d0;
          border: 1px solid #4ade80;
        }
        .legend-item.replace .legend-color {
          background: #fef08a;
          border: 1px solid #facc15;
        }
        .diff-view-content {
          padding: 20px;
          font-family: 'Noto Sans Devanagari', sans-serif;
          font-size: 1.15rem;
          line-height: 2.2;
          color: #78350f;
          background: #fffef5;
        }
        .diff-segment {
          transition: all 0.2s;
        }
        .diff-segment.equal {
          color: #78350f;
        }
        .diff-segment.delete {
          background: linear-gradient(to bottom, #fecaca, #fca5a5);
          color: #b91c1c;
          padding: 2px 4px;
          border-radius: 4px;
          text-decoration: line-through;
          text-decoration-thickness: 2px;
          margin: 0 1px;
          font-weight: 600;
        }
        .diff-segment.insert {
          background: linear-gradient(to bottom, #bbf7d0, #86efac);
          color: #166534;
          padding: 2px 4px;
          border-radius: 4px;
          margin: 0 1px;
          font-weight: 600;
          border-bottom: 2px solid #22c55e;
        }
        .diff-segment.replace {
          background: linear-gradient(to bottom, #fef08a, #fde047);
          color: #854d0e;
          padding: 2px 4px;
          border-radius: 4px;
          margin: 0 1px;
          font-weight: 600;
        }
        .diff-summary {
          display: flex;
          gap: 20px;
          padding: 12px 20px;
          background: #fef9c3;
          border-top: 1px solid #fde047;
          font-size: 0.8rem;
          color: #854d0e;
        }
        .summary-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .summary-count {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 22px;
          height: 22px;
          padding: 0 6px;
          border-radius: 11px;
          font-weight: 700;
          font-size: 0.75rem;
        }
        .summary-count.delete {
          background: #fecaca;
          color: #b91c1c;
        }
        .summary-count.insert {
          background: #bbf7d0;
          color: #166534;
        }

        /* Comparison Container */
        .comparison-container {
          background: #fff;
          border: 1px solid #e8ddd0;
          border-radius: 16px;
          overflow: hidden;
        }
        .comparison-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 14px 20px;
          background: #fef7ed;
          border-bottom: 1px solid #e8ddd0;
          font-weight: 600;
          color: #78350f;
          font-size: 0.9rem;
        }

        /* Comparison Grid */
        .comparison-grid {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          gap: 0;
        }
        @media (max-width: 768px) {
          .comparison-grid {
            grid-template-columns: 1fr;
          }
          .comparison-arrow {
            transform: rotate(90deg);
            padding: 8px 0 !important;
          }
        }
        .comparison-box {
          padding: 0;
        }
        .comparison-box .box-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 18px;
          border-bottom: 1px solid #f3e8dc;
          font-size: 0.8rem;
          font-weight: 600;
        }
        .comparison-box.yours .box-header {
          background: #fef2f2;
          color: #b91c1c;
        }
        .comparison-box.correct .box-header {
          background: #ecfdf5;
          color: #047857;
        }
        .box-icon {
          font-size: 1rem;
        }
        .box-title {
          flex: 1;
        }
        .box-badge {
          font-size: 0.7rem;
          padding: 3px 8px;
          border-radius: 10px;
          text-transform: uppercase;
        }
        .box-badge.error {
          background: #fecaca;
          color: #b91c1c;
        }
        .copy-btn {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          font-size: 0.75rem;
          background: rgba(16, 185, 129, 0.1);
          color: #047857;
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .copy-btn:hover {
          background: rgba(16, 185, 129, 0.2);
        }
        .box-content {
          padding: 18px;
          font-family: 'Noto Sans Devanagari', sans-serif;
          font-size: 1.05rem;
          line-height: 2;
          color: #78350f;
          min-height: 80px;
        }
        .comparison-box.yours .box-content {
          background: #fffbf8;
        }
        .comparison-box.correct .box-content {
          background: #f8fdfb;
        }
        .error-text {
          background: #fecaca;
          color: #b91c1c;
          padding: 2px 4px;
          border-radius: 4px;
          font-weight: 600;
          text-decoration: underline;
          text-decoration-style: wavy;
          text-decoration-color: #dc2626;
        }

        /* Inline Diff Highlighting */
        .diff-delete {
          background: linear-gradient(to bottom, #fecaca, #fca5a5);
          color: #b91c1c;
          padding: 2px 6px;
          border-radius: 4px;
          text-decoration: line-through;
          text-decoration-thickness: 2px;
          text-decoration-color: #dc2626;
          font-weight: 600;
          margin: 0 2px;
        }
        .diff-insert {
          background: linear-gradient(to bottom, #bbf7d0, #86efac);
          color: #166534;
          padding: 2px 6px;
          border-radius: 4px;
          font-weight: 600;
          border-bottom: 2px solid #22c55e;
          margin: 0 2px;
        }

        /* Diff Summary Bar */
        .diff-summary-bar {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 20px;
          background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%);
          border-top: 1px solid #fde047;
          font-size: 0.8rem;
        }
        .summary-tag {
          display: inline-flex;
          align-items: center;
          padding: 4px 10px;
          border-radius: 12px;
          font-weight: 600;
          margin-right: 8px;
        }
        .summary-tag.delete {
          background: #fecaca;
          color: #b91c1c;
        }
        .summary-tag.insert {
          background: #bbf7d0;
          color: #166534;
        }

        /* Differences Log */
        .differences-log {
          border-top: 1px solid #e8ddd0;
          background: #fefbf6;
        }
        .log-header {
          padding: 12px 20px;
          font-weight: 600;
          font-size: 0.85rem;
          color: #78350f;
          background: #fef7ed;
          border-bottom: 1px solid #f3e8dc;
        }
        .log-content {
          padding: 14px 20px;
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }
        .log-item {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          border-radius: 8px;
          font-size: 0.85rem;
          font-family: 'Noto Sans Devanagari', sans-serif;
        }
        .log-item.delete {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #b91c1c;
        }
        .log-item.insert {
          background: #f0fdf4;
          border: 1px solid #bbf7d0;
          color: #166534;
        }
        .log-item.success {
          background: #ecfdf5;
          border: 1px solid #a7f3d0;
          color: #047857;
        }
        .log-icon {
          font-weight: 700;
          font-size: 1rem;
        }
        .log-label {
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.03em;
          opacity: 0.8;
        }
        .log-text {
          font-weight: 600;
        }

        .comparison-arrow {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0 12px;
          color: #d97706;
          background: #fef7ed;
        }

        /* Differences List */
        .differences-list {
          border-top: 1px solid #e8ddd0;
          padding: 16px 20px;
          background: #fefbf6;
        }
        .diff-header {
          font-size: 0.8rem;
          font-weight: 600;
          color: #78350f;
          margin-bottom: 12px;
        }
        .diff-items {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
        }
        .diff-item {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: #fff;
          border: 1px solid #e8ddd0;
          border-radius: 8px;
          font-size: 0.85rem;
        }
        .diff-wrong {
          color: #dc2626;
          font-weight: 600;
          font-family: 'Noto Sans Devanagari', sans-serif;
        }
        .diff-correct {
          color: #059669;
          font-weight: 600;
          font-family: 'Noto Sans Devanagari', sans-serif;
        }
        .diff-arrow {
          color: #92400e;
        }
        .diff-label {
          font-size: 0.75rem;
          color: #78350f;
        }
        .diff-more {
          font-size: 0.8rem;
          color: #92400e;
          padding: 6px 12px;
        }

        /* Perfect Match Box */
        .perfect-match-box {
          background: #f0fdf4;
          border: 1px solid #a7f3d0;
          border-radius: 14px;
          overflow: hidden;
        }
        .match-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 14px 18px;
          background: #dcfce7;
          border-bottom: 1px solid #a7f3d0;
          color: #047857;
          font-weight: 600;
          font-size: 0.9rem;
        }
        .match-header .copy-btn {
          margin-left: auto;
        }
        .match-content {
          padding: 20px;
          font-family: 'Noto Sans Devanagari', sans-serif;
          font-size: 1.1rem;
          line-height: 2;
          color: #065f46;
        }

        /* Not Found Section */
        .not-found-section {
          text-align: center;
          padding: 40px 20px;
        }
        .not-found-icon {
          width: 80px;
          height: 80px;
          margin: 0 auto 16px;
          background: #fef3c7;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #d97706;
        }
        .not-found-section h4 {
          margin: 0 0 8px 0;
          font-size: 1.2rem;
          color: #78350f;
        }
        .not-found-section > p {
          margin: 0;
          color: #92400e;
          font-size: 0.9rem;
        }

        /* Suggestions */
        .suggestions {
          margin-top: 24px;
          text-align: left;
        }
        .suggestions-title {
          font-weight: 600;
          color: #78350f;
          font-size: 0.9rem;
          margin-bottom: 12px;
        }
        .suggestion-item {
          padding: 14px;
          background: #fff;
          border: 1px solid #e8ddd0;
          border-radius: 12px;
          margin-bottom: 10px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .suggestion-item:hover {
          border-color: #d97706;
          box-shadow: 0 2px 8px rgba(217, 119, 6, 0.1);
        }
        .suggestion-text {
          font-family: 'Noto Sans Devanagari', sans-serif;
          font-size: 0.95rem;
          color: #78350f;
          line-height: 1.6;
          margin-bottom: 8px;
        }
        .suggestion-meta {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 0.75rem;
          color: #92400e;
        }
        .match-percent {
          margin-left: auto;
          padding: 2px 8px;
          background: #fef3c7;
          border-radius: 10px;
          font-weight: 600;
          color: #b45309;
        }
      `;
