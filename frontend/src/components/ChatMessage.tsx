import React from 'react';
import { Message } from '../types';
import { Citation } from './Citation';
import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
    message: Message;
    onCitationClick: (citation: any) => void;
}

export function ChatMessage({ message, onCitationClick }: ChatMessageProps) {
    const isUser = message.role === 'user';
    
    return (
        <div className={`py-6 flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex flex-shrink-0 items-center justify-center mt-1">
                    <Bot className="w-5 h-5" />
                </div>
            )}
            
            <div className={`max-w-[80%] ${isUser ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-5 py-3.5' : ''}`}>
                <div className={`prose prose-sm dark:prose-invert max-w-none ${isUser ? 'text-primary-foreground' : 'text-foreground'}`}>
                    {message.content.split('\n').map((line, i) => (
                        <p key={i} className={line ? 'mb-2' : 'mb-0'}>{line}</p>
                    ))}
                </div>
                
                {message.citations && message.citations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-border/50">
                        <p className="text-xs font-medium text-muted-foreground mb-2">SOURCES</p>
                        <div className="flex flex-wrap">
                            {message.citations.map((cit, idx) => (
                                <Citation key={`${cit.chunk_id}-${idx}`} citation={cit} index={idx} onClick={onCitationClick} />
                            ))}
                        </div>
                    </div>
                )}
            </div>
            
            {isUser && (
                <div className="w-8 h-8 rounded-full bg-muted flex flex-shrink-0 items-center justify-center mt-1">
                    <User className="w-5 h-5 opacity-70" />
                </div>
            )}
        </div>
    );
}
