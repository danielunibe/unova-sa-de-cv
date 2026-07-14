import React, { useState, useEffect, useRef, useCallback } from 'react';
import CustomCursor from './components/CustomCursor';
import TitleBar from './components/TitleBar';
import BentoGrid from './components/BentoGrid';
import PanningDotsBackground from './components/PanningDotsBackground';

const MIN_WIDTH = 640;
const MIN_HEIGHT = 480;

const App: React.FC = () => {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  
  const windowRef = useRef<HTMLDivElement>(null);
  const isResizingRef = useRef(false);
  const isDraggingRef = useRef(false);
  
  const resizeHandleRef = useRef<string | null>(null);
  const initialPosRef = useRef({ x: 0, y: 0 }); // Mouse initial pos for resize
  const initialSizeRef = useRef({ width: 0, height: 0 }); // Window size for resize
  const initialWindowPosRef = useRef({ x: 0, y: 0 }); // Window pos for resize
  const dragStartOffsetRef = useRef({ x: 0, y: 0 }); // Offset for drag

  useEffect(() => {
    const setInitialState = () => {
      const maxWidth = 1024;
      const maxHeight = 768;
      const padding = 32;
      const initialWidth = Math.min(window.innerWidth - padding, maxWidth);
      const initialHeight = Math.min(window.innerHeight - padding, maxHeight);
      
      setSize({ width: initialWidth, height: initialHeight });
      setPosition({
        x: (window.innerWidth - initialWidth) / 2,
        y: (window.innerHeight - initialHeight) / 2
      });
    };
    setInitialState();

    // Safety: Handle window resize to keep app in bounds
    const handleWindowResize = () => {
        setPosition(prev => {
            const newX = Math.min(prev.x, window.innerWidth - 100);
            const newY = Math.min(prev.y, window.innerHeight - 100);
            return { x: Math.max(0, newX), y: Math.max(0, newY) };
        });
    };
    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, []);
  
  // Drag Logic
  const handleTitleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    setIsDragging(true);
    
    // Calculate offset relative to the window's top-left corner
    dragStartOffsetRef.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y
    };
    
    window.addEventListener('mousemove', handleDragMove);
    window.addEventListener('mouseup', handleDragUp);
  }, [position]);

  const handleDragMove = useCallback((e: MouseEvent) => {
    if (!isDraggingRef.current) return;
    
    const newX = e.clientX - dragStartOffsetRef.current.x;
    const newY = e.clientY - dragStartOffsetRef.current.y;

    // Boundary Constraints (AAA Polish): 
    // Allow window to go partially offscreen but keep title bar accessible.
    // X: Keep at least 50px visible. Y: Keep title bar (approx 55px) from going above viewport.
    const constrainedX = newX; 
    const constrainedY = Math.max(0, newY); 

    setPosition({ x: constrainedX, y: constrainedY });
  }, []);

  const handleDragUp = useCallback(() => {
    isDraggingRef.current = false;
    setIsDragging(false);
    window.removeEventListener('mousemove', handleDragMove);
    window.removeEventListener('mouseup', handleDragUp);
  }, [handleDragMove]);

  // Resize Logic
  const handleResizeMouseDown = (e: React.MouseEvent<HTMLDivElement>, handle: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    isResizingRef.current = true;
    resizeHandleRef.current = handle;
    initialPosRef.current = { x: e.clientX, y: e.clientY };
    initialSizeRef.current = { ...size };
    initialWindowPosRef.current = { ...position };
    
    window.addEventListener('mousemove', handleResizeMove);
    window.addEventListener('mouseup', handleResizeUp);
  };

  const handleResizeMove = useCallback((e: MouseEvent) => {
    if (!isResizingRef.current || !resizeHandleRef.current) return;

    const dx = e.clientX - initialPosRef.current.x;
    const dy = e.clientY - initialPosRef.current.y;

    const startW = initialSizeRef.current.width;
    const startH = initialSizeRef.current.height;
    const startX = initialWindowPosRef.current.x;
    const startY = initialWindowPosRef.current.y;

    let newW = startW;
    let newH = startH;
    let newX = startX;
    let newY = startY;

    if (resizeHandleRef.current.includes('right')) {
      newW = Math.max(startW + dx, MIN_WIDTH);
    }
    if (resizeHandleRef.current.includes('left')) {
      const proposedWidth = startW - dx;
      newW = Math.max(proposedWidth, MIN_WIDTH);
      newX = startX + (startW - newW);
    }
    if (resizeHandleRef.current.includes('bottom')) {
      newH = Math.max(startH + dy, MIN_HEIGHT);
    }
    if (resizeHandleRef.current.includes('top')) {
      const proposedHeight = startH - dy;
      newH = Math.max(proposedHeight, MIN_HEIGHT);
      newY = startY + (startH - newH);
    }
    
    setSize({ width: newW, height: newH });
    setPosition({ x: newX, y: newY });
  }, []);

  const handleResizeUp = useCallback(() => {
    isResizingRef.current = false;
    resizeHandleRef.current = null;
    window.removeEventListener('mousemove', handleResizeMove);
    window.removeEventListener('mouseup', handleResizeUp);
  }, [handleResizeMove]);

  const resizeHandles = [
    { handle: 'top', class: 'top-[-5px] left-5 right-5 h-[15px]' },
    { handle: 'bottom', class: 'bottom-[-5px] left-5 right-5 h-[15px]' },
    { handle: 'left', class: 'left-[-5px] top-5 bottom-5 w-[15px]' },
    { handle: 'right', class: 'right-[-5px] top-5 bottom-5 w-[15px]' },
    { handle: 'top-left', class: 'top-[-5px] left-[-5px] w-[20px] h-[20px]' },
    { handle: 'top-right', class: 'top-[-5px] right-[-5px] w-[20px] h-[20px]' },
    { handle: 'bottom-left', class: 'bottom-[-5px] left-[-5px] w-[20px] h-[20px]' },
    { handle: 'bottom-right', class: 'bottom-[-5px] right-[-5px] w-[20px] h-[20px]' }
  ];

  return (
    <>
      <CustomCursor />
      <div 
        ref={windowRef}
        className={`
            will-change-transform
            backdrop-blur-lg backdrop-saturate-[1.1] 
            relative rounded-[24px] border-[5px] 
            flex flex-col overflow-hidden 
            transition-[box-shadow,transform,opacity,background-color,border-color] 
            ${isDragging 
                ? 'bg-[#1E1E1E]/85 border-[#2a2a2a] shadow-[0_50px_100px_rgba(0,0,0,0.6),_0_30px_60px_rgba(0,0,0,0.4)] scale-[1.02] duration-200 ease-out' 
                : 'bg-[#1E1E1E]/80 border-[#222222] shadow-[0_20px_40px_rgba(0,0,0,0.3),_0_10px_30px_rgba(0,0,0,0.2)] scale-100 duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)]'
            }
        `}
        style={{
          position: 'absolute',
          left: `${position.x}px`,
          top: `${position.y}px`,
          width: `${size.width}px`,
          height: `${size.height}px`,
          opacity: size.width === 0 ? 0 : 1,
          transform: size.width === 0 ? 'scale(0.95)' : undefined,
        }}
      >
        <PanningDotsBackground windowPosition={position} />
        
        <TitleBar onMouseDown={handleTitleMouseDown} />

        <div className="relative z-[1] flex-grow overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[120px] bg-gradient-to-b from-[#222222]/80 to-transparent z-[3] pointer-events-none" />
          <div className="relative z-[4] w-full h-full pt-[55px] p-4 pointer-events-none">
            <BentoGrid />
          </div>
        </div>
        
        {/* Resize Handles */}
        {resizeHandles.map(({ handle, class: tailwindClass }) => (
          <div
            key={handle}
            className={`absolute z-10 bg-transparent ${tailwindClass}`}
            onMouseDown={e => handleResizeMouseDown(e, handle)}
          />
        ))}
      </div>
    </>
  );
};

export default App;