import React from 'react';
import { Citation as CitationType } from '../types';

interface CitationProps {
    citation: CitationType;
    index: number;
    onClick: (citation: CitationType) => void;
}

export function Citation({ citation, index, onClick }: CitationProps) {
    return (
        <button 
            onClick={() => onClick(citation)}
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-primary/10 text-primary hover:bg-primary/20 text-xs font-medium transition-colors border border-primary/20 mr-1.5 mb-1.5"
            title={`${citation.source_file} (Page ${citation.page})`}
        >
            <span className="opacity-60 text-[10px]">[{index + 1}]</span>
            <span className="truncate max-w-[150px]">{citation.source_file}</span>
            {citation.page && <span className="opacity-70">p.{citation.page}</span>}
        </button>
    );
}
