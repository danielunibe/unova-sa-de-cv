
import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { LUCIDE_ICONS } from '../constants';
import { IconData } from '../types';

interface Square {
    id: string;
    icon: IconData;
}

interface Column {
    id: string;
    squares: Square[];
}

const AnimatedGrid: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [grid, setGrid] = useState<Column[]>([]);
    const scrollPositions = useRef<number[]>([]);
    const animationFrameId = useRef<number | null>(null);
    const lastTimestamp = useRef<number>(0);
    const scrollSpeed = 15; // pixels per second

    const shuffledIcons = useMemo(() => 
        [...LUCIDE_ICONS].sort(() => 0.5 - Math.random()), 
    []);

    const generateGrid = useCallback(() => {
        if (!containerRef.current) return;
        const { offsetWidth: containerWidth, offsetHeight: containerHeight } = containerRef.current;
        if (containerWidth === 0 || containerHeight === 0) return;

        const squareSize = 68;
        const gap = 12;
        const cellSize = squareSize + gap;
        const cols = Math.ceil(containerWidth / cellSize) + 2;
        const rows = Math.ceil(containerHeight / cellSize) + 2;

        let iconIndex = 0;
        const newGrid: Column[] = [];
        const newScrollPositions: number[] = [];

        for (let i = 0; i < cols; i++) {
            const squares: Square[] = [];
            for (let j = 0; j < rows; j++) {
                squares.push({
                    id: `sq-${i}-${j}`,
                    icon: shuffledIcons[iconIndex++ % shuffledIcons.length],
                });
            }
            newGrid.push({ id: `col-${i}`, squares });

            // Initial position for upward scroll
            const columnHeight = rows * cellSize - gap;
            const initialPos = i % 2 !== 0 ? -columnHeight : 0;
            newScrollPositions.push(initialPos);
        }
        
        setGrid(newGrid);
        scrollPositions.current = newScrollPositions;
    }, [shuffledIcons]);

    const animate = useCallback((timestamp: number) => {
        if (lastTimestamp.current === 0) {
            lastTimestamp.current = timestamp;
        }
        const deltaTime = (timestamp - lastTimestamp.current) / 1000;
        lastTimestamp.current = timestamp;
        const movement = scrollSpeed * deltaTime;

        const newPositions = scrollPositions.current.map((pos, i) => {
            const direction = i % 2 === 0 ? 1 : -1;
            let newPos = pos + movement * direction;

            const column = containerRef.current?.children[i] as HTMLElement;
            if (column) {
                const columnHeight = column.offsetHeight / 2;
                 if (direction === 1 && newPos >= 0) {
                    newPos -= columnHeight;
                 }
                 if (direction === -1 && newPos <= -columnHeight) {
                   newPos += columnHeight;
                 }
            }
            return newPos;
        });

        scrollPositions.current = newPositions;

        if (containerRef.current) {
            Array.from(containerRef.current.children).forEach((col, i) => {
                (col as HTMLElement).style.transform = `translateY(${scrollPositions.current[i]}px)`;
            });
        }

        animationFrameId.current = requestAnimationFrame(animate);
    }, []);

    useEffect(() => {
        generateGrid();
        const resizeObserver = new ResizeObserver(() => generateGrid());
        if (containerRef.current) {
            resizeObserver.observe(containerRef.current);
        }
        
        animationFrameId.current = requestAnimationFrame(animate);

        return () => {
            if (animationFrameId.current) {
                cancelAnimationFrame(animationFrameId.current);
            }
            resizeObserver.disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [generateGrid]);
    
    return (
        <div ref={containerRef} className="absolute inset-0 z-10 overflow-hidden pointer-events-none flex justify-center gap-3">
            {grid.map((col) => (
                <div key={col.id} className="bg-column flex flex-col gap-3 flex-shrink-0">
                    {/* Duplicate content for infinite scroll */}
                    {[...col.squares, ...col.squares].map((sq, sqIndex) => (
                         <div key={`${sq.id}-${sqIndex}`} className="bg-[#2D2D2D] rounded-[20px] w-[68px] h-[68px] flex items-center justify-center text-[color:var(--text-secondary)] transition-opacity duration-300 ease-in-out flex-shrink-0">
                             <svg className="w-1/2 h-1/2 opacity-30" style={{strokeWidth: 1}} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
                                <g dangerouslySetInnerHTML={{ __html: sq.icon.path }} />
                             </svg>
                         </div>
                    ))}
                </div>
            ))}
        </div>
    );
};

export default AnimatedGrid;
