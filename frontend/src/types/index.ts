export interface DocumentMetadata {
    id: string;
    name: string;
    type: string;
    pages: number;
    status: string;
}

export interface Citation {
    source_file: string;
    page: number | null;
    chunk_id: string;
}

export interface ChatResponse {
    answer: string;
    citations: Citation[];
    debug: any;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    citations?: Citation[];
    debug?: any;
}
