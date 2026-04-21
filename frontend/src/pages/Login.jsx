import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { Bot, Mail, Lock, AlertCircle, UserPlus, LogIn } from 'lucide-react';

export default function Login() {
    const [isRegistering, setIsRegistering] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleAuth = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const endpoint = isRegistering ? '/auth/register' : '/auth/login';
            const res = await api.post(endpoint, { email, password });

            if (res.data.status === 'success') {
                localStorage.setItem('session_id', res.data.session_id);
                localStorage.setItem('user_id', res.data.user_id);
                navigate('/chat');
            }
        } catch (err) {
            if (err.response?.data?.detail) {
                setError(err.response.data.detail);
            } else {
                setError('Server error. Ensure FastAPI is running and Firebase is connected.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: 'flex', width: '100%', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
            <div className="glass-panel animate-fade-in" style={{ padding: '40px', width: '100%', maxWidth: '400px' }}>
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <div style={{ display: 'inline-flex', padding: '16px', background: 'var(--glass-border)', borderRadius: '50%', marginBottom: '16px' }}>
                        <Bot size={32} color="var(--accent)" />
                    </div>
                    <h2 style={{ fontSize: '24px', fontWeight: '700' }}>
                        {isRegistering ? 'Create your Account' : 'Welcome Back'}
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                        {isRegistering ? 'Register to access your DSL workspace' : 'Sign in to access your DSL workspace'}
                    </p>
                </div>

                {error && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '12px', borderRadius: '8px', marginBottom: '20px' }}>
                        <AlertCircle size={18} />
                        <span style={{ fontSize: '14px' }}>{error}</span>
                    </div>
                )}

                <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    <div style={{ position: 'relative' }}>
                        <Mail size={18} color="var(--text-secondary)" style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)' }} />
                        <input
                            type="email"
                            placeholder="Email"
                            className="glass-input"
                            style={{ paddingLeft: '44px' }}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div style={{ position: 'relative' }}>
                        <Lock size={18} color="var(--text-secondary)" style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)' }} />
                        <input
                            type="password"
                            placeholder="Password"
                            className="glass-input"
                            style={{ paddingLeft: '44px' }}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button type="submit" className="glass-button" disabled={loading} style={{ marginTop: '8px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px' }}>
                        {loading ? 'Processing...' : isRegistering ? <><UserPlus size={18} /> Register</> : <><LogIn size={18} /> Sign In</>}
                    </button>
                </form>

                <div style={{ marginTop: '24px', textAlign: 'center' }}>
                    <button
                        type="button"
                        onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
                        style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                        {isRegistering ? 'Already registered? Sign in here' : "Don't have an account? Register here"}
                    </button>
                </div>
            </div>
        </div>
    );
}
