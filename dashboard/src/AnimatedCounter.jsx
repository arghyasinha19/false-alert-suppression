import React, { useState, useEffect, useRef } from 'react';

/**
 * AnimatedCounter
 * Smoothly animates numbers from 0 to N or interpolates between values
 * using cubic ease-out over `duration` ms.
 */
function AnimatedCounter({ value, duration = 800, decimals = 0, suffix = '' }) {
  const numericTarget = typeof value === 'number' ? value : parseFloat(value) || 0;
  const [displayValue, setDisplayValue] = useState(0);
  const prevTargetRef = useRef(0);
  const animFrameRef = useRef(null);

  useEffect(() => {
    const startVal = prevTargetRef.current;
    const endVal = numericTarget;
    prevTargetRef.current = endVal;

    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease-out: 1 - (1 - progress)^3
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = startVal + (endVal - startVal) * ease;

      setDisplayValue(current);

      if (progress < 1) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayValue(endVal);
      }
    };

    animFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [numericTarget, duration]);

  const formatted = decimals > 0
    ? displayValue.toFixed(decimals)
    : Math.round(displayValue).toLocaleString();

  return (
    <span className="animated-counter" title={`${formatted}${suffix}`}>
      {formatted}{suffix}
    </span>
  );
}

export default AnimatedCounter;
