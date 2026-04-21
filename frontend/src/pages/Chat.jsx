import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Send, LogOut, Paperclip, Bot, User, Upload } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

export default function Chat() {
    const [messages, setMessages] = useState([{ role: 'assistant', text: 'Hello! Upload your base documents and ask me anything. My memory tracks the last 50 queries.' }]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();

    const sessionId = localStorage.getItem('session_id');
    const userId = localStorage.getItem('user_id');

    useEffect(() => {
        if (!sessionId) navigate('/login');
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, navigate, sessionId]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userQuery = input.trim();
        setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
        setInput('');
        setLoading(true);

        try {
            const res = await api.post('/chat', { session_id: sessionId, user_id: userId, query: userQuery });
            setMessages(prev => [...prev, { role: 'assistant', text: res.data.response }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', text: 'Error: Could not reach the UniversalRAG engine.' }]);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);

        try {
            const res = await api.post('/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setMessages(prev => [...prev, { role: 'assistant', text: `Document ${res.data.filename} has been routed to the ${res.data.route?.engine || 'backend'} engine by cell/type rules.` }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', text: 'Error uploading document.' }]);
        } finally {
            setUploading(false);
            e.target.value = null; // reset
        }
    };

    const handleLogout = async () => {
        try {
            const fd = new FormData();
            fd.append('session_id', sessionId);
            await api.post('/auth/logout', fd);
        } catch { }
        localStorage.clear();
        navigate('/login');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100%' }}>
            {/* Header */}
            <header className="glass-panel" style={{ borderRadius: '0', borderTop: 'none', borderLeft: 'none', borderRight: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Bot color="var(--accent)" />
                    <h1 style={{ fontSize: '18px', fontWeight: '600' }}>UniversalRAG Orchestrator</h1>
                </div>
                <button onClick={handleLogout} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <LogOut size={18} />
                    <span>Logout</span>
                </button>
            </header>

            {/* Main Chat Area */}
            <main style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {messages.map((msg, i) => (
                    <div key={i} className="animate-fade-in" style={{ display: 'flex', gap: '16px', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
                        {msg.role === 'assistant' && (
                            <div style={{ minWidth: '36px', height: '36px', borderRadius: '50%', background: 'var(--glass-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--glass-border)' }}>
                                <Bot size={20} color="var(--accent)" />
                            </div>
                        )}
                        <div className={`glass-panel ${msg.role === 'user' ? 'user-msg' : 'bot-msg'}`} style={{ padding: '16px', background: msg.role === 'user' ? 'var(--accent)' : 'var(--glass-bg)', border: msg.role === 'user' ? 'none' : '' }}>
                            <div style={{ lineHeight: '1.6', overflowWrap: 'break-word', wordBreak: 'break-word' }}>
                                {msg.role === 'user' ? (
                                    msg.text
                                ) : (
                                    <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                                        {msg.text}
                                    </ReactMarkdown>
                                )}
                            </div>
                        </div>
                        {msg.role === 'user' && (
                            <div style={{ minWidth: '36px', height: '36px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <User size={20} />
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="animate-fade-in" style={{ alignSelf: 'flex-start', padding: '16px', color: 'var(--text-secondary)' }}>
                        <span style={{ animation: 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite' }}>Reasoning over top 5 contexts and 50 past queries...</span>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </main>

            {/* Input Area */}
            <footer style={{ padding: '24px', background: 'var(--bg-gradient)', borderTop: '1px solid var(--glass-border)' }}>
                <form onSubmit={handleSend} style={{ display: 'flex', gap: '12px', maxWidth: '1000px', margin: '0 auto' }}>
                    <input type="file" ref={fileInputRef} style={{ display: 'none' }} onChange={handleFileUpload} />

                    <button type="button" onClick={() => fileInputRef.current?.click()} className="glass-button" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 16px', background: 'var(--glass-bg)' }} disabled={uploading} title="Upload Base Document (CSV >150 routed to Chroma)">
                        {uploading ? <Upload size={20} className="animate-pulse" /> : <Paperclip size={20} />}
                    </button>

                    <input
                        type="text"
                        className="glass-input"
                        placeholder="Type 'VERIFY: Overheat THEN ValveOpened' or mathematical inquiries..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        disabled={loading}
                    />

                    <button type="submit" className="glass-button" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 20px' }} disabled={loading || !input.trim()}>
                        <Send size={20} />
                    </button>
                </form>
            </footer>
        </div>
    );
}
