import React, { useState } from 'react';
import { auth } from '../../firebase';
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    GoogleAuthProvider,
    signInWithPopup
} from 'firebase/auth';
import { FaUser, FaLock, FaGoogle } from 'react-icons/fa';
import { IoSparkles } from "react-icons/io5";
import { useNavigate } from 'react-router-dom';
import '../styles/auth.css';


const Auth = () => {
    const navigate = useNavigate()
    const [isLoginView, setIsLoginView] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(''); // State for success message
    const [loading, setLoading] = useState(false);
    const [googleLoading, setGoogleLoading] = useState(false);

    const handleAuthAction = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess(''); // Clear previous messages

        try {
            if (isLoginView) {
                await signInWithEmailAndPassword(auth, email, password);
                setSuccess('Login successful! Redirecting...');
                setTimeout(() => {
                    navigate(`/dashboard`)
                }, 2000);
            } else {
                await createUserWithEmailAndPassword(auth, email, password);
                setSuccess('Account created! Redirecting...');
                setTimeout(() => {
                    navigate(`/dashboard`)
                }, 2000);
            }
        } catch (err) {
            if (err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password' || err.code === 'auth/invalid-credential') {
                setError('Invalid email or password.');
            } else if (err.code === 'auth/email-already-in-use') {
                setError('An account with this email already exists.');
            } else {
                setError('An error occurred. Please try again.');
            }
            console.error("Firebase auth error:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSignIn = async () => {
        setGoogleLoading(true);
        setError('');
        setSuccess(''); // Clear previous messages
        const provider = new GoogleAuthProvider();
        try {
            await signInWithPopup(auth, provider);
            setSuccess('Login successful! Redirecting...');
            // --- THIS IS THE FIX ---
            // Add the same redirect logic to the Google sign-in handler.
            setTimeout(() => {
                navigate(`/dashboard`);
            }, 2000);
            // --- END OF FIX ---
        } catch (err) {
            setError('Could not sign in with Google. Please try again.');
            console.error("Google sign-in error:", err);
        } finally {
            setGoogleLoading(false);
        }
    };

    return (
        <div className="auth-page-container">
            <div className="auth-card">
                <div className="auth-header">
                    <IoSparkles className="auth-logo-icon" />
                    <h1>Welcome to DruvAI</h1>
                    <p>{isLoginView ? 'Sign in to continue to your personal assistant.' : 'Create an account to get started.'}</p>
                </div>

                {error && <p className="auth-error">{error}</p>}
                {success && <p className="auth-success">{success}</p>}

                <form onSubmit={handleAuthAction} className="auth-form">
                    <div className="input-group">
                        <FaUser className="input-icon" />
                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <FaLock className="input-icon" />
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <button type="submit" className="auth-button" disabled={loading || googleLoading}>
                        {loading ? 'Processing...' : (isLoginView ? 'Sign In' : 'Sign Up')}
                    </button>
                </form>

                <div className="auth-divider">
                    <span>OR</span>
                </div>

                <button onClick={handleGoogleSignIn} className="google-auth-button" disabled={loading || googleLoading}>
                    {googleLoading ? (
                        'Signing in...'
                    ) : (
                        <>
                            <FaGoogle />
                            {isLoginView ? <span>Signin with Google</span> : <span>Signup with Google</span>}
                        </>
                    )}
                </button>


                <div className="auth-toggle">
                    <p>
                        {isLoginView ? "Don't have an account?" : "Already have an account?"}
                        <button onClick={() => { setIsLoginView(!isLoginView); setError(''); setSuccess(''); }}>
                            {isLoginView ? 'Sign Up' : 'Sign In'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Auth;
