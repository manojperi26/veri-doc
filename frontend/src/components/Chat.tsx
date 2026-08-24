import React, { useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Message } from '../types';
import { ChatMessage } from './ChatMessage';
import { api } from '../services/api';

interface ChatProps {
    messages: Message[];
    setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
    onDebugData: (data: any) => void;
    hasDocuments: boolean;
}

export function Chat({ messages, setMessages, onDebugData, hasDocuments }: ChatProps) {
    const [input, setInput] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, loading]);

    const handleSend = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || !hasDocuments || loading) return;

        const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await api.chat(userMsg.content);
            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: res.answer,
                citations: res.citations,
            };
            setMessages(prev => [...prev, aiMsg]);
            if (res.debug) {
                onDebugData(res.debug);
            }
        } catch (error) {
            console.error(error);
            const aiMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "An error occurred while communicating with the server.",
            };
            setMessages(prev => [...prev, aiMsg]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-full relative">
            {!hasDocuments && messages.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center p-8 max-w-2xl mx-auto">
                    <h2 className="text-3xl font-bold tracking-tight mb-3">Your documents, now searchable.</h2>
                    <p className="text-muted-foreground mb-8 text-lg">Upload documents in the sidebar to turn them into a grounded AI knowledge base.</p>
                </div>
            ) : (
                <div className="flex-1 overflow-y-auto px-4 md:px-8 pt-16 pb-32">
                    <div className="max-w-3xl mx-auto w-full">
                        {messages.length === 0 && (
                            <div className="py-20 text-center opacity-50">
                                <p>Ask your documents anything.</p>
                            </div>
                        )}
                        {messages.map(msg => (
                            <ChatMessage key={msg.id} message={msg} onCitationClick={() => {}} />
                        ))}
                        {loading && (
                            <div className="py-6 flex justify-start">
                                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center mt-1">
                                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>
            )}

            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-background via-background to-transparent pt-10 pb-6 px-4 md:px-8">
                <div className="max-w-3xl mx-auto w-full">
                    <form 
                        onSubmit={handleSend}
                        className="relative flex items-center shadow-lg bg-card border border-border rounded-xl overflow-hidden focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all"
                    >
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={hasDocuments ? "Ask a question..." : "Upload documents to begin"}
                            disabled={!hasDocuments || loading}
                            className="w-full max-h-40 min-h-[60px] py-4 pl-4 pr-14 bg-transparent outline-none resize-none text-sm placeholder:text-muted-foreground disabled:opacity-50"
                            rows={1}
                        />
                        <button 
                            type="submit"
                            disabled={!input.trim() || !hasDocuments || loading}
                            className="absolute right-3 bottom-3 p-2 rounded-lg bg-primary text-primary-foreground disabled:opacity-50 disabled:bg-muted disabled:text-muted-foreground transition-colors hover:bg-primary/90"
                        >
                            <Send className="w-4 h-4" />
                        </button>
                    </form>
                    <p className="text-center text-xs text-muted-foreground mt-3">
                        Answers are generated strictly from your uploaded documents.
                    </p>
                </div>
            </div>
        </div>
    );
}
