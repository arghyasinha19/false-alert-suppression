import React, { useRef, useState, useEffect, useCallback } from 'react';

/**
 * TableScrollWrapper
 * ------------------
 * Enforces independent scroll bounds with:
 * - 28px left and right edge gradient masks indicating overflow (D-09, D-11)
 * - Dynamic scroll listener toggling 'has-overflow-left' and 'has-overflow-right' (D-10)
 * - Bottom clearance (8px) ensuring horizontal scrollbars are fully unblocked (D-09)
 * - Support for optional maxHeight constraint (D-13)
 */
export default function TableScrollWrapper({
  children,
  className = '',
  maxHeight = null
}) {
  const containerRef = useRef(null);
  const [hasOverflowLeft, setHasOverflowLeft] = useState(false);
  const [hasOverflowRight, setHasOverflowRight] = useState(false);

  const checkOverflow = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const { scrollLeft, scrollWidth, clientWidth } = el;
    // Buffer of 2px to handle sub-pixel rendering rounding
    setHasOverflowLeft(scrollLeft > 2);
    setHasOverflowRight(scrollLeft + clientWidth < scrollWidth - 2);
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    checkOverflow();

    el.addEventListener('scroll', checkOverflow, { passive: true });

    let resizeObserver = null;
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => {
        checkOverflow();
      });
      resizeObserver.observe(el);
    }

    const handleWindowResize = () => checkOverflow();
    window.addEventListener('resize', handleWindowResize);

    return () => {
      el.removeEventListener('scroll', checkOverflow);
      if (resizeObserver) resizeObserver.disconnect();
      window.removeEventListener('resize', handleWindowResize);
    };
  }, [checkOverflow]);

  return (
    <div
      className={`table-scroll-wrapper ${hasOverflowLeft ? 'has-overflow-left' : ''} ${hasOverflowRight ? 'has-overflow-right' : ''} ${className}`}
    >
      <div
        ref={containerRef}
        className="table-scroll-container"
        style={maxHeight ? { maxHeight } : undefined}
      >
        {children}
      </div>
    </div>
  );
}
