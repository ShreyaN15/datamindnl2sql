'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './AuthProvider';

export default function AuthScreen() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isLogin) {
        const response = await api.auth.login(username, password);
        login(response.user.id, response.user.username, response.user.email);
      } else {
        const response = await api.auth.register(username, email, password, fullName);
        login(response.id, response.username, response.email);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-white selection:bg-black selection:text-white">
      <div className="w-full max-w-5xl grid gap-16 lg:grid-cols-2 items-center">
        {/* Left Column - Copy */}
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-mono tracking-wide text-gray-600 rounded-md">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-black opacity-40"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-black"></span>
            </span>
            V 0.1 / AI Workspace
          </div>
          <div className="space-y-4">
            <h1 className="text-5xl font-medium tracking-tight text-black leading-tight">
              Turn natural language <span className="text-gray-400">into production SQL.</span>
            </h1>
            <p className="text-lg text-gray-500 font-light max-w-lg leading-relaxed">
              DataMind securely translates plain English into efficient query operations, visualizing the results inside a refined interface.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-6 text-sm text-gray-500 font-medium">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              Schema-aware
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              Instant charts
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              Read-only operations
            </div>
          </div>
        </div>

        {/* Right Column - Form */}
        <div className="relative w-full max-w-md mx-auto lg:ml-auto">
          <div className="bg-white p-8 sm:p-10 border border-gray-200 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl">
            <div className="mb-8">
              <h2 className="text-2xl font-medium text-black">
                {isLogin ? 'Welcome back' : 'Create an account'}
              </h2>
              <p className="mt-2 text-sm text-gray-500">
                {isLogin ? 'Enter your details to access your workspace.' : 'Set up your workspace in seconds.'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-1">
                <label className="text-sm font-medium text-black">Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-transparent border-b border-gray-300 py-2.5 text-black placeholder:text-gray-400 focus:border-black focus:outline-none transition-colors"
                  placeholder="your-handle"
                  required
                />
              </div>

              {!isLogin && (
                <>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-black">Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full bg-transparent border-b border-gray-300 py-2.5 text-black placeholder:text-gray-400 focus:border-black focus:outline-none transition-colors"
                      placeholder="name@company.com"
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium text-black">Full name</label>
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="w-full bg-transparent border-b border-gray-300 py-2.5 text-black placeholder:text-gray-400 focus:border-black focus:outline-none transition-colors"
                      placeholder="Jane Doe"
                    />
                  </div>
                </>
              )}

              <div className="space-y-1">
                <label className="text-sm font-medium text-black">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-transparent border-b border-gray-300 py-2.5 text-black placeholder:text-gray-400 focus:border-black focus:outline-none transition-colors"
                  placeholder="••••••••"
                  required
                />
              </div>

              {error && (
                <div className="text-sm text-red-600 bg-red-50 p-3 flex items-start gap-2 rounded-md">
                  <svg className="w-5 h-5 text-red-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-black text-white py-3 px-4 text-sm font-medium hover:bg-gray-900 transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-black disabled:opacity-50 disabled:cursor-not-allowed rounded-lg"
                >
                  {loading ? 'Processing...' : isLogin ? 'Sign In' : 'Sign Up'}
                </button>
              </div>
            </form>

            <div className="mt-6 text-center text-sm text-gray-500">
              {isLogin ? (
                <p>
                  Don't have an account?{' '}
                  <button onClick={() => setIsLogin(false)} className="text-black font-medium hover:underline">
                    Sign up
                  </button>
                </p>
              ) : (
                <p>
                  Already have an account?{' '}
                  <button onClick={() => setIsLogin(true)} className="text-black font-medium hover:underline">
                    Sign in
                  </button>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
