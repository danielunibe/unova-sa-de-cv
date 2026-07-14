
import React, { memo } from 'react';

interface Props {
  windowPosition: { x: number; y: number };
}

const PanningDotsBackground: React.FC<Props> = memo(({ windowPosition }) => {
  return (
    <div
      className="absolute inset-0 z-0 pointer-events-none"
      style={{
        backgroundImage: 'radial-gradient(circle at center, rgba(255, 255, 255, 0.1) 1.5px, transparent 2px)',
        backgroundSize: '28px 28px',
        // Invert the window position so the background stays "fixed" relative to the screen
        backgroundPosition: `${-windowPosition.x}px ${-windowPosition.y}px`,
        // Hardware acceleration hint
        willChange: 'background-position',
      }}
    />
  );
});

PanningDotsBackground.displayName = 'PanningDotsBackground';

export default PanningDotsBackground;
