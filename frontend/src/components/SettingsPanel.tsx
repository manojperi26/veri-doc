import React, { useState, useEffect } from 'react';
import { Key, Check, AlertCircle, Loader2, Eye, EyeOff, Sparkles } from 'lucide-react';
import { api } from '../services/api';

interface SettingsPanelProps {
    onConfigured: () => void;
}

export function SettingsPanel({ onConfigured }: SettingsPanelProps) {
    const [groqKey, setGroqKey] = useState(() => sessionStorage.getItem('veridoc_groq_key') || '');
    const [hfKey, setHfKey] = useState(() => sessionStorage.getItem('veridoc_huggingface_key') || '');
    
    const [groqOk, setGroqOk] = useState(false);
    const [hfOk, setHfOk] = useState(false);
    const [saving, setSaving] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');
    const [error, setError] = useState('');
    const [showGroq, setShowGroq] = useState(false);
    const [showHf, setShowHf] = useState(false);

    useEffect(() => {
        // Remove keys saved by earlier versions. Provider keys must not survive
        // beyond the active browser session in client-side storage.
        localStorage.removeItem('veridoc_groq_key');
        localStorage.removeItem('veridoc_google_key');
        localStorage.removeItem('veridoc_huggingface_key');

        // Only check server status to show green checkmarks — do NOT auto-close the panel
        api.getConfigStatus().then((res) => {
            setGroqOk(res.groq_configured);
            setHfOk(res.huggingface_configured);
        }).catch(() => {});
        
        // Re-sync current-session keys if the backend was restarted.
        const savedGroq = sessionStorage.getItem('veridoc_groq_key');
        const savedHf = sessionStorage.getItem('veridoc_huggingface_key');
        
        if (savedGroq || savedHf) {
            api.updateKeys(savedGroq || undefined, savedHf || undefined).then((status) => {
                setGroqOk(status.groq_configured);
                setHfOk(status.huggingface_configured);
                // Do NOT call onConfigured() here — let the user see the panel and decide
            }).catch(() => {});
        }
    }, []);

    const handleSave = async () => {
        if (!groqKey.trim() && !hfKey.trim()) {
            setError('Please enter at least one API key (Groq or Hugging Face).');
            return;
        }
        
        setSaving(true);
        setError('');
        setSuccessMsg('');
        
        try {
            // Persist only for the current browser session; durable browser storage
            // unnecessarily exposes provider keys to later local users and XSS.
            if (groqKey.trim()) {
                sessionStorage.setItem('veridoc_groq_key', groqKey.trim());
            }
            if (hfKey.trim()) {
                sessionStorage.setItem('veridoc_huggingface_key', hfKey.trim());
            }

            const res = await api.updateKeys(
                groqKey.trim() || undefined,
                hfKey.trim() || undefined
            );
            
            setGroqOk(res.groq_configured);
            setHfOk(res.huggingface_configured);
            setSuccessMsg('API keys saved successfully! Redirecting...');
            
            // Short delay so user sees the success message before panel closes
            if (res.groq_configured || res.huggingface_configured) {
                setTimeout(() => {
                    onConfigured();
                }, 1000);
            }
        } catch (e: any) {
            setError(e?.response?.data?.detail || 'Failed to save keys.');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="max-w-lg w-full mx-auto my-8 p-6 bg-card border border-border rounded-xl shadow-2xl">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Key className="w-5 h-5 text-primary" />
                </div>
                <div>
                    <h2 className="text-lg font-semibold tracking-tight">AI Provider Configuration</h2>
                    <p className="text-xs text-muted-foreground">Configure your LLM providers with automatic fallback</p>
                </div>
            </div>

            <div className="space-y-5">
                {/* Groq API Key (Primary) */}
                <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                        <label className="text-sm font-medium flex items-center gap-1.5">
                            <span>Groq API Key</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/20 text-primary font-semibold">PRIMARY</span>
                        </label>
                        {groqOk && (
                            <span className="text-xs text-green-400 flex items-center gap-1">
                                <Check className="w-3.5 h-3.5" /> Connected
                            </span>
                        )}
                    </div>
                    <div className="relative">
                        <input
                            type={showGroq ? 'text' : 'password'}
                            value={groqKey}
                            onChange={(e) => setGroqKey(e.target.value)}
                            placeholder="gsk_..."
                            className="w-full px-3.5 py-2.5 pr-10 bg-background border border-border rounded-lg text-sm outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary placeholder:text-muted-foreground/40 font-mono"
                        />
                        <button
                            type="button"
                            onClick={() => setShowGroq(!showGroq)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            tabIndex={-1}
                        >
                            {showGroq ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground">Ultra-fast inference (Llama 3.3 70B & Llama 3.1 8B).</p>
                </div>

                {/* Hugging Face API Key (Backup) */}
                <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                        <label className="text-sm font-medium flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                            <span>Hugging Face API Key</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold">BACKUP</span>
                        </label>
                        {hfOk && (
                            <span className="text-xs text-green-400 flex items-center gap-1">
                                <Check className="w-3.5 h-3.5" /> Connected
                            </span>
                        )}
                    </div>
                    <div className="relative">
                        <input
                            type={showHf ? 'text' : 'password'}
                            value={hfKey}
                            onChange={(e) => setHfKey(e.target.value)}
                            placeholder="hf_..."
                            className="w-full px-3.5 py-2.5 pr-10 bg-background border border-border rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 placeholder:text-muted-foreground/40 font-mono"
                        />
                        <button
                            type="button"
                            onClick={() => setShowHf(!showHf)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            tabIndex={-1}
                        >
                            {showHf ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                    </div>
                    <p className="text-[11px] text-muted-foreground">Automatic backup if Groq reaches rate/token limit (Zephyr, Llama, Mistral).</p>
                </div>

                {error && (
                    <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                {successMsg && (
                    <div className="flex items-center gap-2 text-xs text-green-400 bg-green-500/10 border border-green-500/20 p-3 rounded-lg">
                        <Check className="w-4 h-4 flex-shrink-0" />
                        <span>{successMsg}</span>
                    </div>
                )}

                <button
                    onClick={handleSave}
                    disabled={saving || (!groqKey.trim() && !hfKey.trim())}
                    className="w-full py-2.5 rounded-lg bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-sm"
                >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Key className="w-4 h-4" />}
                    {saving ? 'Saving & Verifying...' : 'Save API Keys'}
                </button>
            </div>
        </div>
    );
}
