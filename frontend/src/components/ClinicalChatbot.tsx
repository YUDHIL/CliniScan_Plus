'use client';

import React, { useState, useEffect, useRef } from 'react';
import { UserSession } from '../types';
import { api } from '../lib/api';
import {
  MessageSquare,
  Sparkles,
  X,
  Send,
  Trash2,
  Bot,
  User,
  ChevronDown,
  Minimize2,
  Maximize2,
  HelpCircle,
  ExternalLink,
  ShieldAlert,
  CheckCircle2,
  Stethoscope,
  HeartPulse,
  CornerDownLeft,
  Volume2
} from 'lucide-react';

interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ClinicalChatbotProps {
  user?: UserSession | null;
  activeScanSummary?: string;
}

const QUICK_PROMPTS = [
  'What is Cardiomegaly and what should I do?',
  'How do I book an appointment with a pulmonologist?',
  'Explain Pleural Effusion vs Pneumothorax',
  'How does the YOLO11 X-ray model work?',
  'Find top chest hospitals in my city',
  'What does a normal chest radiograph report mean?',
];

export const ClinicalChatbot: React.FC<ClinicalChatbotProps> = ({
  user,
  activeScanSummary,
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [inputValue, setInputValue] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [hasUnread, setHasUnread] = useState<boolean>(false);
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [isExpandedFull, setIsExpandedFull] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load chat history from localStorage on initial mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem('cliniscan_chat_history');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setMessages(parsed);
          return;
        }
      }
    } catch (e) {
      console.warn('Failed to load chat history', e);
    }

    // Default welcome message with clear formatting
    const welcomeMsg: ChatMessageItem = {
      id: 'welcome-1',
      role: 'assistant',
      content:
        `👋 **Hello! I'm your CliniScan AI Clinical Assistant.**\n\n` +
        `I am connected to Google Gemini and trained on chest radiograph diagnostics. I can help you with:\n` +
        `- 🫁 **Understanding X-ray findings** (Cardiomegaly, Effusion, Atelectasis, Pneumothorax, etc.)\n` +
        `- 👨‍⚕️ **Finding & booking top verified specialists** in your city\n` +
        `- 📍 **Directions to hospitals & clinic GPS navigation**\n` +
        `- 📑 **Interpreting confidence scores & lab diagnostic reports**\n\n` +
        `How can I assist you with your health or diagnostics today? Tap any suggestion below or ask anything!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages([welcomeMsg]);
  }, []);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0) {
      try {
        localStorage.setItem('cliniscan_chat_history', JSON.stringify(messages));
      } catch (e) {
        console.warn('Failed to save chat history', e);
      }
    }
  }, [messages]);

  // Scroll to bottom of message list
  useEffect(() => {
    if (isOpen && !isMinimized) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isMinimized, isExpandedFull]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && !isMinimized) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 150);
      setHasUnread(false);
    }
  }, [isOpen, isMinimized]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputValue).trim();
    if (!query || isLoading) return;

    const userMsg: ChatMessageItem = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Build history for context
      const history = messages.slice(-8).map((m) => ({
        role: m.role === 'user' ? 'user' : 'model',
        content: m.content,
      }));

      // Context
      const context: Record<string, any> = {
        user_name: user?.full_name,
        user_role: user?.role || 'Patient',
        user_city: user?.city,
        active_findings: activeScanSummary,
      };

      const res = await api.sendChatMessage({
        message: query,
        history,
        context,
      });

      const assistantMsg: ChatMessageItem = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: res.reply || 'I am here to assist with your medical queries.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (!isOpen) {
        setHasUnread(true);
      }
    } catch (err: any) {
      const errorMsg: ChatMessageItem = {
        id: `bot-err-${Date.now()}`,
        role: 'assistant',
        content:
          `I apologize, but I encountered a temporary connection issue. Please feel free to ask again, or review specialist recommendations on the directory.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = () => {
    if (confirm('Are you sure you want to clear your conversation history?')) {
      const resetMsg: ChatMessageItem = {
        id: `welcome-${Date.now()}`,
        role: 'assistant',
        content: 'Conversation history cleared. How may I assist you now?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages([resetMsg]);
      localStorage.removeItem('cliniscan_chat_history');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Helper to format simple markdown (bold, lists, code) into readable JSX
  const renderFormattedContent = (content: string) => {
    return (
      <div className="space-y-2 text-sm sm:text-[15px] leading-relaxed break-words font-normal">
        {content.split('\n').map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) {
            return <div key={idx} className="h-1.5" />;
          }

          // Bullet points
          if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const bulletText = trimmed.replace(/^[-*]\s+/, '');
            return (
              <div key={idx} className="flex items-start space-x-2.5 pl-1.5 py-0.5">
                <span className="text-sky-500 font-extrabold text-base leading-none select-none mt-0.5">&bull;</span>
                <span className="flex-1" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(bulletText) }} />
              </div>
            );
          }

          // Numbered lists
          if (/^\d+\.\s+/.test(trimmed)) {
            const num = trimmed.match(/^\d+\./)?.[0];
            const listText = trimmed.replace(/^\d+\.\s+/, '');
            return (
              <div key={idx} className="flex items-start space-x-2.5 pl-1.5 py-0.5">
                <span className="text-sky-600 font-extrabold font-mono text-xs select-none bg-sky-100 px-1.5 py-0.5 rounded-md mt-0.5">{num}</span>
                <span className="flex-1" dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(listText) }} />
              </div>
            );
          }

          return (
            <p
              key={idx}
              className="py-0.5"
              dangerouslySetInnerHTML={{ __html: formatInlineMarkdown(trimmed) }}
            />
          );
        })}
      </div>
    );
  };

  const formatInlineMarkdown = (text: string) => {
    let formatted = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong class="font-extrabold text-slate-900">$1</strong>');
    
    // Italic: *text* or _text_
    formatted = formatted.replace(/\*(.*?)\*/g, '<em class="italic text-slate-700">$1</em>');

    // Code: `code`
    formatted = formatted.replace(/`(.*?)`/g, '<code class="bg-slate-200/90 text-sky-900 px-1.5 py-0.5 rounded text-xs font-mono font-bold">$1</code>');

    return formatted;
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end pointer-events-none">
      {/* EXPANDED CHAT WINDOW (LARGE & VISIBLE) */}
      {isOpen && (
        <div
          className={`pointer-events-auto bg-white/98 backdrop-blur-2xl rounded-3xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden transition-all duration-300 mb-3 ${
            isExpandedFull
              ? 'w-[calc(100vw-2rem)] sm:w-[680px] md:w-[740px] h-[calc(100vh-4rem)] max-h-[850px]'
              : isMinimized
              ? 'w-[calc(100vw-2rem)] sm:w-[520px] h-16'
              : 'w-[calc(100vw-2rem)] sm:w-[500px] md:w-[540px] xl:w-[560px] h-[680px] max-h-[calc(100vh-5rem)]'
          }`}
          style={{
            boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.25), 0 0 0 1px rgba(226, 232, 240, 0.9)',
          }}
        >
          {/* Header (Rich, spacious, clear) */}
          <div className="bg-gradient-to-r from-sky-950 via-sky-900 to-indigo-950 px-5 py-4 text-white flex items-center justify-between flex-shrink-0 shadow-md select-none border-b border-sky-800/40">
            <div className="flex items-center space-x-3.5">
              <div className="relative">
                <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-sky-400 via-sky-500 to-indigo-500 flex items-center justify-center shadow-lg text-white font-bold">
                  <Sparkles className="w-6 h-6 animate-pulse" />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-400 border-2 border-sky-950 rounded-full"></span>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="font-heading font-extrabold text-base sm:text-lg tracking-tight text-white">
                    CliniScan AI Medical Assistant
                  </h4>
                  <span className="bg-sky-400/25 text-sky-200 text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full border border-sky-300/30">
                    Gemini Live
                  </span>
                </div>
                <p className="text-xs text-sky-200/90 font-medium mt-0.5">
                  {isLoading ? 'Analyzing medical knowledge...' : 'Clinical Radiology & Specialist Guidance'}
                </p>
              </div>
            </div>

            {/* Header controls */}
            <div className="flex items-center space-x-1.5">
              <button
                type="button"
                onClick={handleClearHistory}
                title="Clear Chat History"
                className="p-2 text-sky-200 hover:text-white hover:bg-white/15 rounded-xl transition cursor-pointer"
              >
                <Trash2 className="w-4.5 h-4.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsExpandedFull(!isExpandedFull)}
                title={isExpandedFull ? 'Standard View' : 'Maximize Window'}
                className="p-2 text-sky-200 hover:text-white hover:bg-white/15 rounded-xl transition cursor-pointer"
              >
                {isExpandedFull ? <Minimize2 className="w-4.5 h-4.5" /> : <Maximize2 className="w-4.5 h-4.5" />}
              </button>
              <button
                type="button"
                onClick={() => setIsMinimized(!isMinimized)}
                title={isMinimized ? 'Expand' : 'Minimize'}
                className="p-2 text-sky-200 hover:text-white hover:bg-white/15 rounded-xl transition cursor-pointer"
              >
                <ChevronDown className={`w-5 h-5 transition-transform ${isMinimized ? 'rotate-180' : ''}`} />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close Assistant"
                className="p-2 text-sky-200 hover:text-white hover:bg-white/15 rounded-xl transition cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Body when not minimized */}
          {!isMinimized && (
            <>
              {/* Message List (Spacious & Readable) */}
              <div className="flex-1 p-5 sm:p-6 overflow-y-auto space-y-5 bg-slate-50/70 scroll-smooth">
                {messages.map((msg) => {
                  const isUser = msg.role === 'user';
                  return (
                    <div
                      key={msg.id}
                      className={`flex items-start gap-3 sm:gap-3.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                    >
                      {/* Avatar */}
                      <div
                        className={`w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex items-center justify-center flex-shrink-0 font-bold shadow-sm ${
                          isUser
                            ? 'bg-sky-600 text-white'
                            : 'bg-gradient-to-br from-indigo-700 via-sky-700 to-teal-700 text-white shadow-md'
                        }`}
                      >
                        {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                      </div>

                      {/* Bubble */}
                      <div
                        className={`max-w-[86%] sm:max-w-[84%] rounded-3xl px-4 sm:px-5 py-3.5 sm:py-4 shadow-sm ${
                          isUser
                            ? 'bg-sky-600 text-white rounded-tr-xs font-medium text-sm sm:text-base leading-relaxed'
                            : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-xs shadow-md shadow-slate-200/50'
                        }`}
                      >
                        {isUser ? (
                          <div className="whitespace-pre-wrap">{msg.content}</div>
                        ) : (
                          renderFormattedContent(msg.content)
                        )}
                        <div
                          className={`text-[10px] sm:text-[11px] mt-2 font-mono font-medium text-right ${
                            isUser ? 'text-sky-200' : 'text-slate-400'
                          }`}
                        >
                          {msg.timestamp}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex items-start gap-3.5">
                    <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-2xl bg-gradient-to-br from-indigo-700 to-sky-700 text-white flex items-center justify-center flex-shrink-0 shadow-md">
                      <Bot className="w-5 h-5 animate-pulse" />
                    </div>
                    <div className="bg-white border border-slate-200 rounded-3xl rounded-tl-xs px-5 py-4 shadow-sm flex items-center space-x-2">
                      <div className="w-2.5 h-2.5 bg-sky-600 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                      <div className="w-2.5 h-2.5 bg-indigo-600 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                      <div className="w-2.5 h-2.5 bg-sky-400 rounded-full animate-bounce"></div>
                      <span className="text-xs sm:text-sm text-slate-500 font-semibold pl-1.5">Consulting Clinical AI Intelligence...</span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Quick suggestion chips (Larger and easily clickable) */}
              <div className="px-4 py-2.5 bg-white border-t border-slate-100 flex items-center space-x-2 overflow-x-auto no-scrollbar flex-shrink-0">
                <span className="text-xs font-extrabold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5 flex-shrink-0 pl-1">
                  <Sparkles className="w-3.5 h-3.5 text-sky-600" />
                  <span>Suggestions:</span>
                </span>
                {QUICK_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSendMessage(prompt)}
                    disabled={isLoading}
                    className="flex-shrink-0 text-xs sm:text-[13px] font-semibold bg-slate-50 hover:bg-sky-50 text-slate-700 hover:text-sky-700 border border-slate-200 hover:border-sky-300 px-3 py-1.5 rounded-xl transition cursor-pointer disabled:opacity-50 active:scale-95 shadow-2xs"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              {/* Input Area (Generous padding, large fonts, clear buttons) */}
              <div className="p-4 sm:p-5 bg-white border-t border-slate-100 flex-shrink-0 space-y-2">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex items-center space-x-2.5"
                >
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask anything about findings, doctors, or symptoms..."
                    disabled={isLoading}
                    className="flex-1 bg-slate-50 hover:bg-white focus:bg-white border border-slate-300 focus:border-sky-600 rounded-2xl px-4 py-3 text-sm sm:text-base font-medium focus:ring-4 focus:ring-sky-500/15 transition outline-none shadow-inner"
                  />
                  <button
                    type="submit"
                    disabled={!inputValue.trim() || isLoading}
                    className="w-12 h-12 bg-sky-600 hover:bg-sky-700 disabled:opacity-40 text-white rounded-2xl flex items-center justify-center transition active:scale-95 shadow-lg shadow-sky-600/25 cursor-pointer flex-shrink-0"
                    title="Send Message"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </form>

                {/* Disclaimer */}
                <div className="flex items-center justify-center space-x-1.5 text-xs text-slate-400 font-medium text-center pt-0.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
                  <span>AI assistance for clinical guidance. Seek emergency care for acute symptoms.</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* FLOATING ACTION BUTTON (PROMINENT & POLISHED) */}
      <button
        type="button"
        onClick={() => {
          setIsOpen(!isOpen);
          setIsMinimized(false);
          setHasUnread(false);
        }}
        className="pointer-events-auto group relative flex items-center space-x-3 bg-gradient-to-r from-sky-900 via-sky-950 to-indigo-950 text-white px-5 py-3.5 rounded-full shadow-2xl border border-sky-400/40 hover:border-sky-300 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer select-none"
        style={{
          boxShadow: '0 12px 30px -5px rgba(14, 116, 144, 0.45), 0 0 20px rgba(56, 189, 248, 0.3)',
        }}
      >
        {/* Animated Bot Avatar */}
        <div className="relative flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sky-400 to-indigo-400 flex items-center justify-center text-slate-950 shadow-inner">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 border-2 border-sky-950 rounded-full animate-ping"></span>
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 border-2 border-sky-950 rounded-full"></span>
        </div>

        {/* Text & Status */}
        <div className="text-left pr-1.5">
          <div className="text-sm font-extrabold tracking-tight flex items-center space-x-2">
            <span>CliniScan AI</span>
            <span className="bg-sky-400/20 text-sky-300 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">24/7 LIVE</span>
          </div>
          <div className="text-xs text-sky-200/90 font-medium">
            {isOpen ? 'Close Chat' : 'Ask Medical Assistant'}
          </div>
        </div>

        {/* Unread badge */}
        {hasUnread && !isOpen && (
          <span className="absolute -top-1 -left-1 bg-red-500 text-white text-xs font-black w-6 h-6 rounded-full flex items-center justify-center border-2 border-white shadow-sm animate-bounce">
            1
          </span>
        )}
      </button>
    </div>
  );
};
