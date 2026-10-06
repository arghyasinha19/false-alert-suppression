import React from 'react';
import { Inbox, RotateCcw } from 'lucide-react';

/**
 * Reusable, accessible EmptyState component conforming to Phase 23 design contract.
 * Used across data tables, topology maps, and inspector panels for consistent zero-match states.
 */
export default function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  compact = false,
  className = '',
}) {
  const defaultIcon = <Inbox size={compact ? 20 : 24} />;

  return (
    <div
      className={`table-empty-state ${compact ? 'empty-state-compact' : ''} ${className}`.trim()}
      role="status"
      aria-live="polite"
    >
      <div className="empty-state-badge" aria-hidden="true">
        {icon || defaultIcon}
      </div>
      <div className="empty-state-title">{title}</div>
      {description && <div className="empty-state-desc">{description}</div>}
      {actionLabel && onAction && (
        <button
          type="button"
          className="empty-state-action"
          onClick={onAction}
        >
          <RotateCcw size={13} style={{ marginRight: '6px' }} />
          <span>{actionLabel}</span>
        </button>
      )}
    </div>
  );
}
