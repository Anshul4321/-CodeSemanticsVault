'use client';

import { useState } from 'react';
import axios from 'axios';

interface Citation {
  filename: string;
  start_line: number;
  end_line: number;
}

interface QueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  retrieved_chunks: number;
}

interface IndexResponse {
  status: string;
  files_indexed: number;
  chunks_created: number;
  size_mb: number;
}

export default function Home() {
  const [repoUrl, setRepoUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [indexed, setIndexed] = useState(false);
  const [indexLoading, setIndexLoading] = useState(false);
  const [currentCollection, setCurrentCollection] = useState('');
  const [indexStats, setIndexStats] = useState<IndexResponse | null>(null);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState('');
  const [darkMode, setDarkMode] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleIndex = async () => {
    if (!repoUrl) {
      setError('Please enter a repository URL');
      return;
    }

    setIndexLoading(true);
    setError('');

    try {
      const collectionName = repoUrl.split('/').pop()?.replace('.git', '') || 'repo';
      const response = await axios.post(`${API_URL}/index`, {
        github_url: repoUrl,
        collection_name: collectionName,
      });

      setIndexStats(response.data);
      setCurrentCollection(collectionName);
      setIndexed(true);
      setQueryResult(null);
      setQuestion('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Indexing failed. Make sure the backend is running on port 8000.');
    } finally {
      setIndexLoading(false);
    }
  };

  const handleNewRepo = () => {
    setIndexed(false);
    setIndexStats(null);
    setQueryResult(null);
    setQuestion('');
    setError('');
    setRepoUrl('');
  };

  const handleQuery = async () => {
    if (!question) {
      setError('Please ask a question');
      return;
    }

    if (!indexed) {
      setError('Please index a repository first');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_URL}/query`, {
        question,
        collection_name: currentCollection,
      });

      setQueryResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`
        @keyframes slowSpin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-slow-spin {
          animation: slowSpin 60s linear infinite;
        }
      `}</style>

      <div className={`min-h-screen transition-colors ${darkMode ? 'dark bg-gray-950' : 'bg-gray-50'}`}>
        {/* Rotating Git Symbol - Right Side */}
        <div className="fixed bottom-8 right-8 opacity-10 pointer-events-none z-0">
          <div className="animate-slow-spin">
            <svg className="w-32 h-32 text-gray-900 dark:text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v 3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </div>
        </div>

        <div className="relative z-10">
          {/* Dark Mode Toggle */}
          <div className="fixed top-4 right-4 z-20">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2 rounded-lg transition ${
                darkMode
                  ? 'bg-gray-900 text-yellow-400 hover:bg-gray-800'
                  : 'bg-white text-gray-800 hover:bg-gray-100 shadow-md'
              }`}
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>

          <div className={`max-w-3xl mx-auto rounded-xl shadow-2xl overflow-hidden transition ${
            darkMode ? 'bg-gray-900' : 'bg-white'
          }`}>
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-teal-600 text-white p-8 text-center">
              <h1 className="text-4xl font-bold mb-2">CodeSemanticsVault</h1>
              <p className="text-blue-100">Ask questions about any GitHub repository</p>
            </div>

            <div className="p-8">
              {/* Index Section */}
              <div className={`mb-8 pb-8 border-b ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                <h2 className={`text-xs font-semibold uppercase tracking-wider mb-4 ${
                  darkMode ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  Step 1: Index Repository
                </h2>
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="e.g., https://github.com/requests/requests"
                  className={`w-full px-4 py-3 mb-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition ${
                    darkMode
                      ? 'bg-gray-800 text-white border border-gray-700 placeholder-gray-500'
                      : 'bg-white text-gray-900 border border-gray-300 placeholder-gray-400'
                  }`}
                />
                <div className="flex gap-3">
                  <button
                    onClick={handleIndex}
                    disabled={indexLoading || indexed}
                    className="flex-1 bg-gradient-to-r from-blue-600 to-teal-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {indexLoading ? 'Indexing...' : indexed ? '✓ Repository Indexed' : 'Index Repository'}
                  </button>
                  {indexed && (
                    <button
                      onClick={handleNewRepo}
                      className={`px-4 py-3 rounded-lg font-semibold transition ${
                        darkMode
                          ? 'bg-gray-800 text-white hover:bg-gray-700 border border-gray-700'
                          : 'bg-gray-100 text-gray-900 hover:bg-gray-200 border border-gray-300'
                      }`}
                    >
                      New Repo
                    </button>
                  )}
                </div>
              </div>

              {/* Status Cards */}
              {indexed && indexStats && (
                <div className={`mb-8 pb-8 border-b ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
                      <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Files Indexed</p>
                      <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {indexStats.files_indexed}
                      </p>
                    </div>
                    <div className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-gray-50'}`}>
                      <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Code Chunks</p>
                      <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {indexStats.chunks_created}
                      </p>
                    </div>
                  </div>
                  <div className={`rounded-lg p-3 text-center text-sm ${
                    darkMode
                      ? 'bg-green-950 border border-green-800 text-green-300'
                      : 'bg-green-50 border border-green-200 text-green-800'
                  }`}>
                    <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                    Repository indexed and ready
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className={`mb-6 rounded-lg p-4 text-sm ${
                  darkMode
                    ? 'bg-red-950 border border-red-800 text-red-300'
                    : 'bg-red-50 border border-red-200 text-red-800'
                }`}>
                  {error}
                </div>
              )}

              {/* Query Section */}
              {indexed && (
                <div className={`mb-8 pb-8 border-b ${darkMode ? 'border-gray-800' : 'border-gray-200'}`}>
                  <h2 className={`text-xs font-semibold uppercase tracking-wider mb-4 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Step 2: Ask a Question
                  </h2>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., How do you make an HTTP request? What is the Session class?"
                    className={`w-full px-4 py-3 mb-4 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none ${
                      darkMode
                        ? 'bg-gray-800 text-white border border-gray-700 placeholder-gray-500'
                        : 'bg-white text-gray-900 border border-gray-300 placeholder-gray-400'
                    }`}
                    rows={4}
                  />
                  <button
                    onClick={handleQuery}
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-blue-600 to-teal-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Searching...' : 'Search & Generate Answer'}
                  </button>
                </div>
              )}

              {/* Answer Section */}
              {queryResult && (
                <div>
                  <h2 className={`text-xs font-semibold uppercase tracking-wider mb-4 ${
                    darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Answer
                  </h2>
                  
                  <div className={`p-6 rounded-lg mb-6 border ${
                    darkMode
                      ? 'bg-gray-800 border-gray-700 text-gray-100'
                      : 'bg-gray-50 border-gray-200 text-gray-800'
                  }`}>
                    <p className="leading-relaxed whitespace-pre-wrap">
                      {queryResult.answer}
                    </p>
                  </div>

                  {queryResult.citations.length > 0 && (
                    <div className="mb-6">
                      <p className={`text-xs font-semibold uppercase tracking-wider mb-3 ${
                        darkMode ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        📍 Source Code
                      </p>
                      <div className="space-y-2">
                        {queryResult.citations.map((citation, idx) => (
                          <div
                            key={idx}
                            className={`rounded-lg p-3 font-mono text-sm transition cursor-pointer ${
                              darkMode
                                ? 'bg-gray-800 border border-gray-700 text-blue-400 hover:bg-gray-700'
                                : 'bg-white border border-gray-300 text-blue-600 hover:bg-gray-50'
                            }`}
                          >
                            {citation.filename}:{citation.start_line}-{citation.end_line}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className={`rounded-lg p-4 text-center border ${
                      darkMode
                        ? 'bg-gray-800 border-gray-700'
                        : 'bg-white border-gray-200'
                    }`}>
                      <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        Confidence Score
                      </p>
                      <p className="text-2xl font-bold text-green-500">
                        {Math.round(queryResult.confidence * 100)}%
                      </p>
                    </div>
                    <div className={`rounded-lg p-4 text-center border ${
                      darkMode
                        ? 'bg-gray-800 border-gray-700'
                        : 'bg-white border-gray-200'
                    }`}>
                      <p className={`text-xs mb-2 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        Retrieved Chunks
                      </p>
                      <p className={`text-2xl font-bold ${darkMode ? 'text-white' : 'text-gray-900'}`}>
                        {queryResult.retrieved_chunks}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}