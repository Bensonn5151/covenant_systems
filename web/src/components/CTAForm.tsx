"use client";

import { ArrowRight, Check, AlertCircle } from 'lucide-react';
import { useState } from 'react';

export default function CTAForm() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('/api/submit-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage('Successfully submitted! We\'ll be in touch.');
        setEmail('');

        // Reset success message after 5 seconds
        setTimeout(() => {
          setStatus('idle');
          setMessage('');
        }, 5000);
      } else {
        setStatus('error');
        setMessage(data.error || 'Failed to submit. Please try again.');
      }
    } catch (error) {
      setStatus('error');
      setMessage('Network error. Please try again.');
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <form className="flex flex-col sm:flex-row gap-3" onSubmit={handleSubmit}>
        <input
          type="email"
          placeholder="ENTER_EMAIL_ADDRESS"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="flex-1 bg-black border border-gray-700 text-green-500 placeholder-gray-600 px-4 py-3 rounded focus:outline-none focus:border-green-500 focus:ring-1 focus:ring-green-500 font-mono text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          required
          disabled={status === 'loading' || status === 'success'}
        />
        <button
          type="submit"
          disabled={status === 'loading' || status === 'success'}
          className="bg-gray-800 hover:bg-green-600 text-white hover:text-black border border-gray-700 hover:border-green-500 px-6 py-3 rounded font-mono text-sm font-bold transition-all duration-300 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-gray-800 disabled:hover:text-white"
        >
          {status === 'loading' ? (
            <>
              <span>[ SUBMITTING... ]</span>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            </>
          ) : status === 'success' ? (
            <>
              <span>[ SUBMITTED ]</span>
              <Check className="w-4 h-4" />
            </>
          ) : (
            <>
              <span>[ SUBMIT_REQUEST ]</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </>
          )}
        </button>
      </form>

      {/* Status Messages */}
      {message && (
        <div className={`mt-3 p-3 rounded flex items-start gap-2 font-mono text-xs ${
          status === 'success'
            ? 'bg-green-500/10 border border-green-500/30 text-green-400'
            : 'bg-red-500/10 border border-red-500/30 text-red-400'
        }`}>
          {status === 'success' ? (
            <Check className="w-4 h-4 flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          )}
          <span>{message}</span>
        </div>
      )}
    </div>
  );
}
