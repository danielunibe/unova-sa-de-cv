
import React, { useEffect, useRef } from 'react';

const CustomCursor: React.FC = () => {
  const cursorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const cursor = cursorRef.current;
    if (!cursor) return;

    const onMouseMove = (e: MouseEvent) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    };

    const onMouseDown = () => {
      cursor.classList.add('jump');
    };

    const onAnimationEnd = () => {
      cursor.classList.remove('jump');
    };

    const onMouseLeave = () => {
        cursor.classList.add('hidden');
    };

    const onMouseEnter = () => {
        cursor.classList.remove('hidden');
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mousedown', onMouseDown);
    cursor.addEventListener('animationend', onAnimationEnd);
    document.body.addEventListener('mouseleave', onMouseLeave);
    document.body.addEventListener('mouseenter', onMouseEnter);

    return () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mousedown', onMouseDown);
      if (cursor) cursor.removeEventListener('animationend', onAnimationEnd);
      document.body.removeEventListener('mouseleave', onMouseLeave);
      document.body.removeEventListener('mouseenter', onMouseEnter);
    };
  }, []);

  return (
    <div 
        ref={cursorRef} 
        className="fixed top-0 left-0 w-10 h-10 pointer-events-none z-[99999] transition-opacity" 
        style={{ transform: 'translate(-8px, -8px)' }}
    >
        <svg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'>
            <defs>
                <filter id='shadow' x='-50%' y='-50%' width='200%' height='200%'>
                    <feDropShadow dx='4' dy='5' stdDeviation='3' floodColor='rgba(0,0,0,0.4)'/>
                </filter>
            </defs>
            <path d='M3.7,2.5l16,11.3l-8,1.4l-3.3,7.6L3.7,2.5z' fill='#FBBF24' stroke='#F3F4F6' strokeWidth='3' strokeLinejoin='round' strokeLinecap='round' filter='url(#shadow)' transform='translate(5 5)'/>
        </svg>
    </div>
  );
};

export default CustomCursor;
