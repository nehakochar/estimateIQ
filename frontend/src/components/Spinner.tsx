import React from 'react';

interface SpinnerProps {
  /** Size in pixels (default: 32) */
  size?: number;
  /** Optional additional className */
  className?: string;
}

export function Spinner({ size = 32, className = '' }: SpinnerProps) {
  return (
    <span
      className={`spinner ${className}`}
      role="status"
      aria-label="Loading"
      style={
        {
          '--spinner-size': `${size}px`,
        } as React.CSSProperties
      }
    />
  );
}
