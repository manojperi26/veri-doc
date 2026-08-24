import axios from 'axios';

const configuredApiUrl = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000/api' : 'https://veri-doc-manoj.onrender.com/api');
const API_URL = configuredApiUrl.replace(/\/+$/, '');

// Maintain persistent session ID
export const getSessionId = (): string => {
    let sid = localStorage.getItem('veridoc_session_id');
    if (!sid) {
        sid = 'session_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
        localStorage.setItem('veridoc_session_id', sid);
    }
    return sid;
};

// Create Axios client with session header interceptor
const client = axios.create({
    baseURL: API_URL,
    timeout: 30_000,
});

client.interceptors.request.use((config) => {
    config.headers['X-Session-ID'] = getSessionId();
    return config;
});

export const api = {
    uploadDocument: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        const res = await client.post('/documents/upload', formData);
        return res.data;
    },
    getDocuments: async () => {
        const res = await client.get('/documents');
        return res.data;
    },
    deleteDocument: async (id: string) => {
        await client.delete(`/documents/${id}`);
    },
    chat: async (query: string) => {
        const res = await client.post('/chat', { query });
        return res.data;
    },
    resetSession: async () => {
        await client.post('/session/reset');
    },
    clearChat: async () => {
        await client.post('/chat/clear');
    },
    getQuestions: async () => {
        const res = await client.get('/documents/questions');
        return res.data;
    },
    getSummary: async (docId: string) => {
        const res = await client.get(`/documents/${docId}/summary`);
        return res.data;
    },
    getConfigStatus: async () => {
        const res = await client.get('/config/status');
        return res.data;
    },
    updateKeys: async (groqKey?: string, hfKey?: string) => {
        const res = await client.post('/config/keys', {
            groq_api_key: groqKey || undefined,
            huggingface_api_key: hfKey || undefined,
        });
        return res.data;
    },
};
