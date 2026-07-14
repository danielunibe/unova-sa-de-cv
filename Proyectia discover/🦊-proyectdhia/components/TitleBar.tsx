import React from 'react';

const WindowControls: React.FC = () => (
  <div className="flex items-center gap-2" onMouseDown={(e) => e.stopPropagation()}>
    <button 
      className="group w-[1.3rem] h-[1.3rem] rounded-md bg-[#3E3E3E] transition-all duration-200 flex items-center justify-center hover:bg-[var(--accent-color)] hover:shadow-lg hover:shadow-yellow-500/30" 
      aria-label="Minimize"
    >
      <svg 
        className="w-[0.8rem] h-[0.8rem] stroke-[2.5] text-[var(--text-secondary)] opacity-0 scale-50 transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 group-hover:text-[#222222]" 
        viewBox="0 0 24 24" fill="none" stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4"></path>
      </svg>
    </button>
    <button 
      className="group w-[1.3rem] h-[1.3rem] rounded-md bg-[#3E3E3E] transition-all duration-200 flex items-center justify-center hover:bg-[var(--danger-color)] hover:shadow-lg hover:shadow-red-500/30" 
      aria-label="Close"
    >
      <svg 
        className="w-[0.8rem] h-[0.8rem] stroke-[2.5] text-[var(--text-secondary)] opacity-0 scale-50 transition-all duration-200 group-hover:opacity-100 group-hover:scale-100 group-hover:text-[#222222]" 
        viewBox="0 0 24 24" fill="none" stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
  </div>
);

interface TitleBarProps {
    onMouseDown?: (e: React.MouseEvent) => void;
}

const TitleBar: React.FC<TitleBarProps> = ({ onMouseDown }) => {
  return (
    <div 
        onMouseDown={onMouseDown}
        className="absolute top-0 left-0 right-0 h-[55px] z-[4] flex items-center justify-between px-3 sm:px-5 select-none"
    >
      <div className="font-bold text-[1.1rem] transition-transform duration-300 ease-in-out hover:scale-105 group cursor-none">
        <span className="text-[color:var(--text-primary)] transition-colors duration-300 group-hover:text-[color:var(--accent-color)]">PROYEC</span>
        
        {/* Brackets: Yellow default, White on Hover */}
        <span className="mx-0.5 text-[color:var(--accent-color)] transition-colors duration-300 group-hover:text-[color:var(--text-primary)]">[</span>
        
        <span className="text-[color:var(--text-primary)] transition-colors duration-300 group-hover:text-[color:var(--accent-color)]">TDH</span>
        
        <span className="mx-0.5 text-[color:var(--accent-color)] transition-colors duration-300 group-hover:text-[color:var(--text-primary)]">]</span>
        
        <span className="text-[color:var(--text-primary)] transition-colors duration-300 group-hover:text-[color:var(--accent-color)]">IA</span>
      </div>
      
      <WindowControls />
    </div>
  );
};

export default TitleBar;