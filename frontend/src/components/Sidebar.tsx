import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, File as FileIcon, Trash2, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { DocumentMetadata } from '../types';

interface SidebarProps {
    documents: DocumentMetadata[];
    onUploadComplete: () => void;
    onReset: () => void;
}

export function Sidebar({ documents, onUploadComplete, onReset }: SidebarProps) {
    const [uploading, setUploading] = React.useState(false);
    
    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;
        const file = e.target.files[0];
        setUploading(true);
        try {
            await api.uploadDocument(file);
            onUploadComplete();
        } catch (error) {
            console.error(error);
            alert("Failed to upload document.");
        } finally {
            setUploading(false);
            e.target.value = ''; // reset
        }
    };

    const handleDelete = async (id: string) => {
        await api.deleteDocument(id);
        onUploadComplete();
    };

    return (
        <div className="w-80 border-r border-black/[0.06] bg-white/60 backdrop-blur-xl flex flex-col h-full">
            <div className="p-6">
                <div className="flex items-center gap-3 mb-2">
                    <div className="w-9 h-9 rounded-xl bg-[#0A84FF] text-white flex items-center justify-center font-bold text-lg shadow-[0_4px_16px_rgba(10,132,255,0.4)]">V</div>
                    <h1 className="text-xl font-bold tracking-tight text-gradient">VeriDoc AI</h1>
                </div>
                <p className="text-sm text-muted-foreground">Grounded Document Intelligence</p>
            </div>
            
            <div className="flex-1 overflow-y-auto px-4">
                <div className="mb-4">
                    <label className="flex items-center justify-center w-full p-4 border-2 border-dashed border-black/10 rounded-2xl hover:border-[#0A84FF]/40 hover:bg-[#0A84FF]/[0.03] cursor-pointer transition-colors duration-200">
                        <span className="flex items-center gap-2 text-sm font-medium">
                            {uploading ? <Loader2 className="w-4 h-4 animate-spin text-[#0A84FF]" /> : <span className="text-lg text-[#0A84FF]">+</span>}
                            Add Documents
                        </span>
                        <input type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.docx,.pptx,.txt" />
                    </label>
                </div>
                
                <div className="space-y-2">
                    <AnimatePresence initial={false}>
                        {documents.map(doc => (
                            <motion.div
                                key={doc.id}
                                initial={{ opacity: 0, y: 6, scale: 0.98 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.96 }}
                                transition={{ duration: 0.25, ease: 'easeOut' }}
                                className="p-3 rounded-xl card-glass card-glass-hover group flex items-start justify-between"
                            >
                                <div className="flex items-start gap-3 overflow-hidden">
                                    <div className="mt-1 text-[#0A84FF] opacity-80">
                                        {doc.type === 'pdf' ? <FileText className="w-4 h-4" /> : <FileIcon className="w-4 h-4" />}
                                    </div>
                                    <div className="overflow-hidden">
                                        <p className="text-sm font-medium truncate" title={doc.name}>{doc.name}</p>
                                        <p className="text-xs text-muted-foreground">{doc.pages} pages • {doc.status}</p>
                                    </div>
                                </div>
                                <button onClick={() => handleDelete(doc.id)} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-black/5 rounded text-muted-foreground transition-all">
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </div>
            
            <div className="p-4 border-t border-black/[0.06] mt-auto">
                <button onClick={onReset} className="w-full py-2 px-4 rounded-xl text-sm font-medium text-white bg-red-500/90 hover:bg-red-500 active:scale-[0.98] transition-all">
                    Reset Session
                </button>
            </div>
        </div>
    );
}
