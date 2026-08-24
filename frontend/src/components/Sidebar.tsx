import React from 'react';
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
        <div className="w-80 border-r border-border bg-card flex flex-col h-full">
            <div className="p-6">
                <div className="flex items-center gap-3 text-primary mb-2">
                    <div className="w-8 h-8 rounded bg-primary text-primary-foreground flex items-center justify-center font-bold text-xl">V</div>
                    <h1 className="text-xl font-bold tracking-tight">VeriDoc AI</h1>
                </div>
                <p className="text-sm text-muted-foreground">Grounded Document Intelligence</p>
            </div>
            
            <div className="flex-1 overflow-y-auto px-4">
                <div className="mb-4">
                    <label className="flex items-center justify-center w-full p-4 border-2 border-dashed border-border rounded-lg hover:border-primary/50 hover:bg-muted/50 cursor-pointer transition-colors">
                        <span className="flex items-center gap-2 text-sm font-medium">
                            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span className="text-lg">+</span>}
                            Add Documents
                        </span>
                        <input type="file" className="hidden" onChange={handleFileChange} accept=".pdf,.docx,.pptx,.txt" />
                    </label>
                </div>
                
                <div className="space-y-2">
                    {documents.map(doc => (
                        <div key={doc.id} className="p-3 rounded-lg border border-border bg-background group flex items-start justify-between">
                            <div className="flex items-start gap-3 overflow-hidden">
                                <div className="mt-1 opacity-70">
                                    {doc.type === 'pdf' ? <FileText className="w-4 h-4" /> : <FileIcon className="w-4 h-4" />}
                                </div>
                                <div className="overflow-hidden">
                                    <p className="text-sm font-medium truncate" title={doc.name}>{doc.name}</p>
                                    <p className="text-xs text-muted-foreground">{doc.pages} pages • {doc.status}</p>
                                </div>
                            </div>
                            <button onClick={() => handleDelete(doc.id)} className="opacity-0 group-hover:opacity-100 p-1 hover:bg-muted rounded text-muted-foreground transition-all">
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    ))}
                </div>
            </div>
            
            <div className="p-4 border-t border-border mt-auto">
                <button onClick={onReset} className="w-full py-2 px-4 rounded text-sm font-medium text-destructive-foreground bg-destructive/90 hover:bg-destructive transition-colors">
                    Reset Session
                </button>
            </div>
        </div>
    );
}
