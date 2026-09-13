import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';
import { SettingsPanel } from './components/SettingsPanel';
import { api } from './services/api';
import { DocumentMetadata, Message } from './types';
import { Info, Settings, FileStack, Sparkles, Quote, ShieldCheck } from 'lucide-react';

function App() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [debugData, setDebugData] = useState<any>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [keysConfigured, setKeysConfigured] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const fetchDocuments = async () => {
    try {
      const docs = await api.getDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error(e);
    }
  };

  const checkConfig = async () => {
    try {
      // Re-sync keys held only for the current browser session after a reload.
      const savedGroq = sessionStorage.getItem('veridoc_groq_key');
      const savedHuggingFace = sessionStorage.getItem('veridoc_huggingface_key');
      
      if (savedGroq || savedHuggingFace) {
        const syncResult = await api.updateKeys(savedGroq || undefined, savedHuggingFace || undefined);
        setKeysConfigured(syncResult.groq_configured || syncResult.huggingface_configured);
      } else {
        const status = await api.getConfigStatus();
        setKeysConfigured(status.groq_configured || status.huggingface_configured);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    checkConfig();
    fetchDocuments();
  }, []);

  const handleReset = async () => {
    if (confirm('Are you sure you want to reset the session? This deletes all documents and history.')) {
      await api.resetSession();
      setDocuments([]);
      setMessages([]);
      setDebugData(null);
    }
  };

  const handleConfigured = () => {
    setKeysConfigured(true);
    setShowSettings(false);
  };

  return (
    <div className="flex h-screen bg-glow text-foreground overflow-hidden font-sans">
      <Sidebar 
        documents={documents} 
        onUploadComplete={fetchDocuments} 
        onReset={handleReset} 
      />
      
      <main className="flex-1 relative overflow-y-auto">
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 rounded-xl border hover:bg-black/5 transition-colors flex items-center gap-2 text-sm ${
              !keysConfigured
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-600 animate-pulse'
                : 'card-glass text-muted-foreground'
            }`}
          >
            <Settings className="w-4 h-4" />
            {!keysConfigured ? 'Set API Keys' : 'Settings'}
          </button>
          {debugData && (
            <button 
              onClick={() => setShowPanel(!showPanel)}
              className="p-2 rounded-xl card-glass hover:bg-black/5 transition-colors flex items-center gap-2 text-sm text-muted-foreground"
            >
              <Info className="w-4 h-4" />
              {showPanel ? 'Hide Details' : 'Retrieval Details'}
            </button>
          )}
        </div>
        
        {showSettings ? (
          <div className="flex items-center justify-center h-full overflow-y-auto p-4">
            <SettingsPanel onConfigured={handleConfigured} />
          </div>
        ) : !keysConfigured ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
            className="flex flex-col items-center justify-center min-h-full text-center px-8 py-16"
          >
            <h1 className="text-5xl font-bold tracking-tight mb-2 text-foreground">
              Your Documents,
              <br />
              <span className="text-gradient">Deeper Insights.</span>
            </h1>
            <p className="text-muted-foreground max-w-md mt-4 mb-10">
              Configure your Groq (Primary) and Hugging Face (Backup) API keys to start asking grounded, cited questions of your own documents.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12 max-w-3xl">
              {[
                { icon: FileStack, title: 'Multiple Formats', sub: 'PDF, DOCX, PPTX, TXT' },
                { icon: Sparkles, title: 'AI-Powered', sub: 'Ask anything about your documents' },
                { icon: Quote, title: 'Citations', sub: 'See exact source and page' },
                { icon: ShieldCheck, title: 'Grounded Answers', sub: 'No hallucinated facts' },
              ].map(({ icon: Icon, title, sub }, i) => (
                <motion.div
                  key={title}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.1 + i * 0.08, ease: 'easeOut' }}
                  className="card-glass card-glass-hover rounded-2xl p-5 flex flex-col items-center text-center"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#0A84FF]/10 border border-[#0A84FF]/15 flex items-center justify-center mb-3">
                    <Icon className="w-5 h-5 text-[#0A84FF]" />
                  </div>
                  <p className="text-sm font-semibold">{title}</p>
                  <p className="text-xs text-muted-foreground mt-1">{sub}</p>
                </motion.div>
              ))}
            </div>

            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setShowSettings(true)}
              className="px-6 py-3 rounded-xl btn-gradient font-medium"
            >
              Configure API Keys
            </motion.button>
          </motion.div>
        ) : (
          <Chat 
            messages={messages} 
            setMessages={setMessages} 
            onDebugData={setDebugData}
            hasDocuments={documents.length > 0} 
          />
        )}
      </main>

      {showPanel && debugData && (
        <aside className="w-80 border-l border-border bg-card p-4 overflow-y-auto">
          <h3 className="text-sm font-semibold mb-4 uppercase tracking-wider text-muted-foreground">Retrieval Details</h3>
          
          <div className="space-y-4 text-sm">
            <div className="p-3 bg-muted/50 rounded-lg border border-border/50">
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground">Query Type:</span>
                <span className="font-medium text-primary">{debugData.query_type}</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground">Retrieval Depth:</span>
                <span className="font-medium">{debugData.retrieval_depth}</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-muted-foreground">Method:</span>
                <span className="font-medium">Hybrid (0.6 / 0.4)</span>
              </div>
            </div>

            <div className="pt-2">
              <h4 className="text-xs font-semibold mb-3 text-muted-foreground">RETRIEVED SOURCES ({debugData.retrieved_sources?.length || 0})</h4>
              <div className="space-y-3">
                {debugData.retrieved_sources?.map((src: any, idx: number) => (
                  <div key={idx} className="p-3 bg-background rounded border border-border text-xs">
                    <div className="flex justify-between mb-2 pb-2 border-b border-border/50">
                      <span className="font-medium truncate max-w-[150px]">{src.metadata.file_name}</span>
                      <span className="text-muted-foreground opacity-70">
                        {src.method} • {(src.score || src.rerank_score || 0).toFixed(2)}
                      </span>
                    </div>
                    <p className="line-clamp-4 text-muted-foreground">{src.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}

export default App;
