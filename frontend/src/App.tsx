import React, { useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Chat } from './components/Chat';
import { SettingsPanel } from './components/SettingsPanel';
import { api } from './services/api';
import { DocumentMetadata, Message } from './types';
import { Info, Settings } from 'lucide-react';

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
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
      <Sidebar 
        documents={documents} 
        onUploadComplete={fetchDocuments} 
        onReset={handleReset} 
      />
      
      <main className="flex-1 relative">
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <button 
            onClick={() => setShowSettings(!showSettings)}
            className={`p-2 rounded-md border border-border hover:bg-muted transition-colors flex items-center gap-2 text-sm text-muted-foreground ${
              !keysConfigured ? 'bg-amber-500/10 border-amber-500/30 text-amber-400 animate-pulse' : 'bg-card'
            }`}
          >
            <Settings className="w-4 h-4" />
            {!keysConfigured ? 'Set API Keys' : 'Settings'}
          </button>
          {debugData && (
            <button 
              onClick={() => setShowPanel(!showPanel)}
              className="p-2 rounded-md bg-card border border-border hover:bg-muted transition-colors flex items-center gap-2 text-sm text-muted-foreground"
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
          <div className="flex flex-col items-center justify-center h-full text-center p-8">
            <h2 className="text-2xl font-bold tracking-tight mb-3">Welcome to VeriDoc AI</h2>
            <p className="text-muted-foreground mb-6">To get started, configure your Groq (Primary) and Hugging Face (Backup) API keys.</p>
            <button
              onClick={() => setShowSettings(true)}
              className="px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors shadow-md"
            >
              Configure API Keys
            </button>
          </div>
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
