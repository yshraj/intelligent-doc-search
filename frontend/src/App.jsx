import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { API_URL, supabase } from './lib/supabase';
import DocumentOrganization from './components/DocumentOrganization';
import './App.css';

function SuccessScreen({ message = "You're all set!", subMessage }) {
  return (
    <div className="success-screen">
      <div className="success-check-wrap">
        <div className="success-check-bg" />
        <div className="success-check">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      </div>
      <p className="success-message">{message}</p>
      {subMessage && <p className="success-sub">{subMessage}</p>}
    </div>
  );
}

function LoaderScreen({ message = 'Loading...' }) {
  return (
    <div className="loader-screen">
      <div className="loader-orb-wrap">
        <div className="loader-orb" />
        <div className="loader-ring loader-ring-1" />
        <div className="loader-ring loader-ring-2" />
        <div className="loader-ring loader-ring-3" />
        <div className="loader-particles">
          {[...Array(8)].map((_, i) => (
            <span key={i} className="loader-particle" style={{ '--i': i }} />
          ))}
        </div>
        <div className="loader-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
      </div>
      <p className="loader-message">{message}</p>
      <div className="loader-dots">
        <span className="loader-dot" />
        <span className="loader-dot" />
        <span className="loader-dot" />
      </div>
    </div>
  );
}

function BrandIcon() {
  return (
    <span className="brand-icon" aria-hidden>
      <svg width="64" height="64" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="mainGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" />
            <stop offset="100%" stopColor="#6366f1" />
          </linearGradient>
          <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
        
        {/* Background circle */}
        <circle cx="20" cy="20" r="18" fill="url(#mainGradient)" opacity="0.1"/>
        
        {/* Document icon - clean and simple */}
        <g transform="translate(10, 8)">
          {/* Document body */}
          <rect x="2" y="0" width="14" height="20" rx="2" fill="url(#mainGradient)" opacity="0.9"/>
          
          {/* Document fold */}
          <path d="M16 5 L16 0 L11 0 L16 5 Z" fill="url(#mainGradient)" opacity="0.6"/>
          
          {/* Document lines */}
          <line x1="5" y1="8" x2="13" y2="8" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
          <line x1="5" y1="11" x2="13" y2="11" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
          <line x1="5" y1="14" x2="10" y2="14" stroke="white" strokeWidth="1.5" strokeLinecap="round" opacity="0.7"/>
        </g>
        
        {/* Chat bubble - positioned at bottom right */}
        <g transform="translate(18, 20)">
          {/* Bubble background */}
          <circle cx="6" cy="6" r="8" fill="white"/>
          <circle cx="6" cy="6" r="7.5" fill="url(#accentGradient)"/>
          
          {/* Chat dots */}
          <circle cx="3" cy="6" r="1.2" fill="white" className="chat-dot dot-1"/>
          <circle cx="6" cy="6" r="1.2" fill="white" className="chat-dot dot-2"/>
          <circle cx="9" cy="6" r="1.2" fill="white" className="chat-dot dot-3"/>
        </g>
      </svg>
    </span>
  );
}

function getOAuthErrorMessage(message) {
  const normalized = (message || '').toLowerCase();
  if (normalized.includes('redirect_uri_mismatch')) {
    return 'Google OAuth redirect URI mismatch. Add your Supabase callback URL in Google Cloud Console and frontend origin in Supabase Redirect URLs.';
  }
  return message || 'Google sign in failed. Try again.';
}

const ROLE_OPTIONS = [
  { id: 'student', label: 'Student', icon: '📚', desc: 'Learning & research' },
  { id: 'developer', label: 'Developer', icon: '💻', desc: 'Docs & code' },
  { id: 'designer', label: 'Designer', icon: '🎨', desc: 'Creative work' },
  { id: 'founder', label: 'Founder', icon: '🚀', desc: 'Building products' },
  { id: 'researcher', label: 'Researcher', icon: '🔬', desc: 'Deep dives' },
  { id: 'content_creator', label: 'Content Creator', icon: '✍️', desc: 'Writing & media' },
  { id: 'educator', label: 'Educator', icon: '👩‍🏫', desc: 'Teaching & training' },
  { id: 'other', label: 'Other', icon: '✨', desc: 'Something else' },
];

// Suggestion chips for single file
const SINGLE_FILE_PROMPTS = [
  'Summarize this document.',
  'What are the key points?',
  'List the main topics covered.',
  'What is the conclusion?',
  'Extract key dates and events.',
  'What are the recommendations?',
  'Identify important definitions.',
  'What questions does this answer?',
  'Find action items.',
  'What are the key takeaways?',
  'Explain the methodology.',
  'What data is presented?',
  'List any statistics mentioned.',
  'What problems are discussed?',
  'What solutions are proposed?',
  'Identify the target audience.',
  'What are the limitations?',
  'Extract contact information.',
  'What references are cited?',
  'Create a brief outline.',
  'What assumptions are made?',
  'Identify technical terms.',
  'What examples are given?',
  'Find contradictions or conflicts.',
  'What is the document structure?',
  'Extract numerical data.',
  'What trends are mentioned?',
  'Identify stakeholders.',
  'What risks are discussed?',
  'Summarize in 3 bullet points.',
];

// Suggestion chips for all files
const ALL_FILES_PROMPTS = [
  'Compare the main themes across documents.',
  'What topics appear in multiple documents?',
  'Find contradictions between documents.',
  'Summarize all documents together.',
  'What are common recommendations?',
  'Compare methodologies used.',
  'Find overlapping information.',
  'What unique insights does each provide?',
  'Create a timeline from all documents.',
  'Compare conclusions across documents.',
  'What data appears in multiple sources?',
  'Identify gaps in coverage.',
  'Which document is most relevant to [topic]?',
  'Compare statistics across documents.',
  'What are the different perspectives?',
  'Find supporting evidence across files.',
  'Which documents agree/disagree?',
  'Create a comprehensive summary.',
  'Compare target audiences.',
  'What patterns emerge across documents?',
  'Identify the most recent information.',
  'Compare recommendations.',
  'What questions remain unanswered?',
  'Find the most detailed explanation.',
  'Compare technical approaches.',
  'What are the key differences?',
  'Synthesize findings from all sources.',
  'Which document provides the best overview?',
  'Compare data quality across documents.',
  'Create a unified action plan.',
];

function getProfileInitErrorMessage(message) {
  const normalized = (message || '').toLowerCase();

  if (
    normalized.includes('missing user_profiles table') ||
    normalized.includes('pgrst205') ||
    normalized.includes('schema cache')
  ) {
    return 'Missing user_profiles table. Run supabase/schema.sql in Supabase SQL Editor.';
  }

  if (normalized.includes('rls policy blocked')) {
    return 'RLS policy blocked profile init. Ensure SELECT/INSERT policies allow auth.uid() = id.';
  }

  if (normalized.includes('missing or invalid authorization') || normalized.includes('authorization must use bearer') || normalized.includes('invalid or expired token')) {
    return 'Your session token is invalid or expired. Sign out and sign in again.';
  }

  return message || 'Profile init failed. Check backend logs.';
}

function parseApiDetail(detail, fallback) {
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const joined = detail.map((item) => item?.msg || item?.message).filter(Boolean).join(', ');
    if (joined) return joined;
  }
  return fallback;
}

function toFriendlyError(error, fallback) {
  const message = typeof error?.message === 'string' ? error.message : '';
  if (!message) return fallback;
  if (message.toLowerCase().includes('cannot read properties')) return fallback;
  return message;
}

function getFileTypeLabel(filename) {
  const lower = (filename || '').toLowerCase();
  if (lower.endsWith('.pdf')) return 'PDF';
  if (lower.endsWith('.txt')) return 'TXT';
  return 'FILE';
}

function formatBytes(bytes) {
  const value = Number(bytes);
  if (!Number.isFinite(value) || value <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const exponent = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  const result = value / (1024 ** exponent);
  return `${result >= 10 ? result.toFixed(0) : result.toFixed(1)} ${units[exponent]}`;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString();
}

function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState('');
  const [initBusy, setInitBusy] = useState(false);
  const [initError, setInitError] = useState('');
  const [showWelcomeForm, setShowWelcomeForm] = useState(false);
  const [showWelcomeBack, setShowWelcomeBack] = useState(false);
  const [nameError, setNameError] = useState('');
  const [roleError, setRoleError] = useState('');
  const [profileUpdateError, setProfileUpdateError] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [userProfile, setUserProfile] = useState(null);
  const [onboardingSubmitting, setOnboardingSubmitting] = useState(false);
  const [onboardingSuccess, setOnboardingSuccess] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState('');
  const [uploadBusy, setUploadBusy] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [deleteBusyId, setDeleteBusyId] = useState('');
  const [chatDocumentId, setChatDocumentId] = useState('all');
  const [chatQuestion, setChatQuestion] = useState('');
  const [chatBusy, setChatBusy] = useState(false);
  const [chatError, setChatError] = useState('');
  const [chatAnswer, setChatAnswer] = useState('');
  const [chatSources, setChatSources] = useState([]);
  const [activeSection, setActiveSection] = useState('documents');
  const [showWelcomeStrip, setShowWelcomeStrip] = useState(true);
  const [usedPrompts, setUsedPrompts] = useState(new Set());
  const [clearAllBusy, setClearAllBusy] = useState(false);
  const [clearAllError, setClearAllError] = useState('');
  const [uploadDuplicate, setUploadDuplicate] = useState(false);
  const [chatSessions, setChatSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState('');
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionDetail, setSessionDetail] = useState(null);
  const [sessionDetailLoading, setSessionDetailLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [conversationMessages, setConversationMessages] = useState([]);
  const [currentPrompts, setCurrentPrompts] = useState([]);
  const [showBackendWarning, setShowBackendWarning] = useState(false);
  const [showOrganizationView, setShowOrganizationView] = useState(false);
  const bootstrappedTokenRef = useRef('');

  // Preflight check for backend availability
  const checkBackendHealth = useCallback(async () => {
    const startTime = Date.now();
    let warningTimeout;

    try {
      // Set a timeout to show warning if it takes more than 5 seconds
      warningTimeout = setTimeout(() => {
        const elapsed = Date.now() - startTime;
        if (elapsed >= 5000) {
          setShowBackendWarning(true);
        }
      }, 5000);

      // Create an AbortController for timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout

      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      clearTimeout(warningTimeout);

      // If response took more than 5 seconds, show the warning briefly
      const elapsed = Date.now() - startTime;
      if (elapsed >= 5000) {
        setShowBackendWarning(true);
        // Auto-hide after 8 seconds
        setTimeout(() => setShowBackendWarning(false), 8000);
      }
    } catch (error) {
      clearTimeout(warningTimeout);
      console.warn('Backend health check failed:', error);
    }
  }, []);

  const initProfile = useCallback(async (accessToken) => {
    if (!accessToken) return;

    setInitBusy(true);
    setInitError('');

    try {
      const response = await fetch(`${API_URL}/profile/init`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const maybeJson = await response.json().catch(() => ({}));
        throw new Error(maybeJson.detail || 'Profile init failed');
      }

      const result = await response.json();
      setUserProfile(result.profile);

      if (result.is_new_user) {
        setShowWelcomeForm(true);
        setShowWelcomeBack(false);
      } else {
        setShowWelcomeBack(true);
        setShowWelcomeForm(false);
      }
    } catch (error) {
      setInitError(getProfileInitErrorMessage(error.message));
    } finally {
      setInitBusy(false);
    }
  }, []);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    // Run preflight check on mount
    checkBackendHealth();

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session);
      if (event === 'SIGNED_OUT') {
        setShowWelcomeForm(false);
        setShowWelcomeBack(false);
        setInitError('');
        setDocuments([]);
        setDocumentsError('');
        setUploadError('');
        setChatDocumentId('all');
        setChatQuestion('');
        setChatError('');
        setChatAnswer('');
        setChatSources([]);
        setActiveSection('documents');
        setShowWelcomeStrip(true);
      }
    });

    return () => subscription?.unsubscribe();
  }, [checkBackendHealth]);

  useEffect(() => {
    if (!session?.access_token) return;
    if (bootstrappedTokenRef.current === session.access_token) return;

    bootstrappedTokenRef.current = session.access_token;
    initProfile(session.access_token);
  }, [initProfile, session?.access_token]);

  const fetchDocuments = useCallback(async () => {
    if (!session?.access_token) return;
    setDocumentsLoading(true);
    setDocumentsError('');

    try {
      const response = await fetch(`${API_URL}/documents`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to load documents'));
      }

      setDocuments(Array.isArray(data) ? data : []);
    } catch (error) {
      setDocumentsError(error.message || 'Failed to load documents');
    } finally {
      setDocumentsLoading(false);
    }
  }, [session?.access_token]);

  useEffect(() => {
    if (!showWelcomeBack || !session?.access_token) return;
    fetchDocuments();
  }, [fetchDocuments, session?.access_token, showWelcomeBack]);

  useEffect(() => {
    if (chatDocumentId === 'all') return;
    if (documents.some((doc) => doc.id === chatDocumentId && doc.status === 'ready')) return;
    setChatDocumentId('all');
  }, [chatDocumentId, documents]);

  useEffect(() => {
    if (!showWelcomeBack || !session?.access_token) return;
    if (!documents.some((doc) => doc.status === 'processing')) return;
    const intervalId = window.setInterval(() => {
      fetchDocuments();
    }, 8000);
    return () => window.clearInterval(intervalId);
  }, [documents, fetchDocuments, session?.access_token, showWelcomeBack]);

  useEffect(() => {
    if (activeSection === 'history' && session?.access_token) {
      fetchChatSessions();
    }
  }, [activeSection, session?.access_token]);

  // Update suggestion prompts only when document scope changes
  useEffect(() => {
    const getRandomPrompts = (promptList, count = 5) => {
      const available = promptList.filter(p => !usedPrompts.has(p));
      if (available.length === 0) {
        // Reset if all used
        setUsedPrompts(new Set());
        return promptList.sort(() => Math.random() - 0.5).slice(0, count);
      }
      return available.sort(() => Math.random() - 0.5).slice(0, count);
    };
    
    const prompts = chatDocumentId === 'all' 
      ? getRandomPrompts(ALL_FILES_PROMPTS)
      : getRandomPrompts(SINGLE_FILE_PROMPTS);
    
    setCurrentPrompts(prompts);
  }, [chatDocumentId, usedPrompts]);

  const handleUploadDocument = async (event) => {
    event.preventDefault();
    if (!session?.access_token || uploadBusy) return;

    const uploadForm = event.currentTarget;
    const formData = new FormData(uploadForm);
    const file = formData.get('file');
    if (!(file instanceof File) || !file.name) {
      setUploadError('Choose a PDF or TXT file first.');
      return;
    }

    setUploadBusy(true);
    setUploadError('');
    setUploadDuplicate(false);
    setDocumentsError('');

    try {
      const requestBody = new FormData();
      requestBody.append('file', file);

      const response = await fetch(`${API_URL}/documents/upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
        body: requestBody,
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to upload document'));
      }

      // Check if this is a duplicate (existing document returned)
      const isDuplicate = documents.some(doc => doc.id === data.id);
      if (isDuplicate) {
        setUploadDuplicate(true);
        // Still update the list to show it's at the top
        setDocuments((current) => [data, ...current.filter((item) => item.id !== data.id)]);
      } else {
        setDocuments((current) => [data, ...current.filter((item) => item.id !== data.id)]);
      }
      
      if (uploadForm && typeof uploadForm.reset === 'function') {
        uploadForm.reset();
      }
    } catch (error) {
      setUploadError(toFriendlyError(error, 'Upload failed. Please try again.'));
    } finally {
      setUploadBusy(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!session?.access_token || !documentId || deleteBusyId) return;

    setDeleteBusyId(documentId);
    setDocumentsError('');

    try {
      const response = await fetch(`${API_URL}/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to delete document'));
      }

      setDocuments((current) => current.filter((doc) => doc.id !== documentId));
      if (chatDocumentId === documentId) {
        setChatDocumentId('all');
      }
    } catch (error) {
      setDocumentsError(toFriendlyError(error, 'Delete failed. Please try again.'));
    } finally {
      setDeleteBusyId('');
    }
  };

  const handleDownloadDocument = async (documentId, filename) => {
    if (!session?.access_token || !documentId) return;

    try {
      const response = await fetch(`${API_URL}/documents/${documentId}/download`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download document');
      }

      // Get the blob from response
      const blob = await response.blob();
      
      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);
      
      // Create a temporary anchor element and trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setDocumentsError(toFriendlyError(error, 'Download failed. Please try again.'));
    }
  };

  const handleChatSubmit = async (event) => {
    event.preventDefault();
    if (!session?.access_token || chatBusy) return;

    const question = chatQuestion.trim();
    if (!question) {
      setChatError('Please enter a question.');
      return;
    }

    setChatBusy(true);
    setChatError('');

    // Add user message to conversation immediately
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: question,
      timestamp: new Date().toISOString(),
    };
    setConversationMessages(prev => [...prev, userMessage]);
    setChatQuestion(''); // Clear input immediately

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          document_id: chatDocumentId,
          session_id: currentSessionId,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to get chat response'));
      }

      // Add assistant message to conversation
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: data.answer || '',
        sources: Array.isArray(data.sources) ? data.sources : [],
        timestamp: new Date().toISOString(),
      };
      setConversationMessages(prev => [...prev, assistantMessage]);
      setCurrentSessionId(data.session_id);
      
      // Keep for backward compatibility
      setChatAnswer(data.answer || '');
      setChatSources(Array.isArray(data.sources) ? data.sources : []);
    } catch (error) {
      setChatError(toFriendlyError(error, 'Chat request failed. Please try again.'));
      // Remove the user message if request failed
      setConversationMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
      setChatQuestion(question); // Restore the question
    } finally {
      setChatBusy(false);
    }
  };

  const handleClearAllDocuments = async () => {
    if (!session?.access_token || clearAllBusy) return;
    
    if (!window.confirm('Are you sure you want to delete ALL your documents? This action cannot be undone.')) {
      return;
    }

    setClearAllBusy(true);
    setClearAllError('');
    setDocumentsError('');

    try {
      const response = await fetch(`${API_URL}/documents/clear-all`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to clear documents'));
      }

      setDocuments([]);
      setChatDocumentId('all');
      setChatQuestion('');
      setChatAnswer('');
      setChatSources([]);
      setUsedPrompts(new Set());
    } catch (error) {
      setClearAllError(toFriendlyError(error, 'Clear all failed. Please try again.'));
    } finally {
      setClearAllBusy(false);
    }
  };

  const fetchChatSessions = async () => {
    if (!session?.access_token) return;
    setSessionsLoading(true);
    setSessionsError('');

    try {
      const response = await fetch(`${API_URL}/history/sessions`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to load sessions'));
      }

      setChatSessions(Array.isArray(data) ? data : []);
    } catch (error) {
      setSessionsError(error.message || 'Failed to load sessions');
    } finally {
      setSessionsLoading(false);
    }
  };

  const fetchSessionDetail = async (sessionId) => {
    if (!session?.access_token) return;
    setSessionDetailLoading(true);

    try {
      const response = await fetch(`${API_URL}/history/sessions/${sessionId}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(parseApiDetail(data.detail, 'Failed to load session'));
      }

      setSessionDetail(data);
      setSelectedSession(sessionId);
    } catch (error) {
      setSessionsError(error.message || 'Failed to load session');
    } finally {
      setSessionDetailLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!session?.access_token) return;
    
    if (!window.confirm('Delete this conversation?')) return;

    try {
      const response = await fetch(`${API_URL}/history/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      setChatSessions(prev => prev.filter(s => s.id !== sessionId));
      if (selectedSession === sessionId) {
        setSelectedSession(null);
        setSessionDetail(null);
      }
    } catch (error) {
      setSessionsError(error.message || 'Failed to delete session');
    }
  };

  const handleClearAllHistory = async () => {
    if (!session?.access_token) return;
    
    if (!window.confirm('Delete ALL chat history? This cannot be undone.')) return;

    try {
      const response = await fetch(`${API_URL}/history/clear-all`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to clear history');
      }

      setChatSessions([]);
      setSelectedSession(null);
      setSessionDetail(null);
    } catch (error) {
      setSessionsError(error.message || 'Failed to clear history');
    }
  };

  const handleSearchHistory = async (query) => {
    if (!session?.access_token || !query.trim()) {
      setSearchResults([]);
      return;
    }

    setSearchLoading(true);

    try {
      const response = await fetch(`${API_URL}/history/search?q=${encodeURIComponent(query)}`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error('Search failed');
      }

      setSearchResults(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleExportHistory = async () => {
    if (!session?.access_token) return;

    try {
      const response = await fetch(`${API_URL}/history/export?format=json`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      });

      const data = await response.json();
      
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `docuchat-history-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      alert('Export failed: ' + error.message);
    }
  };

  const handleResumeSession = (sessionId) => {
    setCurrentSessionId(sessionId);
    setActiveSection('chat');
    setChatQuestion('');
    setChatAnswer('');
    setChatSources([]);
    setConversationMessages([]);
  };

  const handleNewConversation = () => {
    setCurrentSessionId(null);
    setConversationMessages([]);
    setChatQuestion('');
    setChatAnswer('');
    setChatSources([]);
    setChatError('');
  };

  const signInWithGoogle = async () => {
    if (!supabase || authBusy) return;
    setAuthBusy(true);
    setAuthError('');

    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin,
      },
    });

    if (error) {
      setAuthError(getOAuthErrorMessage(error.message));
      setAuthBusy(false);
    }
  };

  const retryInit = () => {
    if (!session?.access_token) return;
    bootstrappedTokenRef.current = '';
    initProfile(session.access_token);
  };

  const signOut = async () => {
    if (!supabase) return;
    await supabase.auth.signOut();
  };

  const handleOnboardingSubmit = async (e) => {
    e.preventDefault();
    setNameError('');
    setRoleError('');
    setProfileUpdateError('');

    const formData = new FormData(e.target);
    const fullName = (formData.get('fullName') || '').trim();
    const company = formData.get('company');

    if (!fullName) {
      setNameError('Please enter your name.');
      return;
    }
    if (!selectedRole) {
      setRoleError('Please select your role.');
      return;
    }

    setOnboardingSubmitting(true);

    try {
      const response = await fetch(`${API_URL}/profile/update`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: fullName,
          company: company || null,
          role: selectedRole,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const detail = data.detail;
        const msg = typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg || d.message).filter(Boolean).join(', ') || 'Failed to update profile'
            : 'Failed to update profile';
        setProfileUpdateError(msg);
        setOnboardingSubmitting(false);
        return;
      }

      setUserProfile(data.profile);
      setOnboardingSubmitting(false);
      setOnboardingSuccess(true);

      // Success animation, then transition
      setTimeout(() => {
        setOnboardingSuccess(false);
        setShowWelcomeForm(false);
        setShowWelcomeBack(true);
      }, 1800);
    } catch (error) {
      console.error('Error updating profile:', error);
      setProfileUpdateError(error.message || 'Failed to update profile');
      setOnboardingSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading-wrap">
          <LoaderScreen message="Loading..." />
        </div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="app">
        {showBackendWarning && (
          <div className="backend-warning-toast">
            <div className="toast-icon">⏳</div>
            <div className="toast-content">
              <strong>Backend is waking up</strong>
              <p>Free Render instance is spinning up. First request may take 30-60 seconds.</p>
            </div>
            <button 
              type="button" 
              className="toast-close" 
              onClick={() => setShowBackendWarning(false)}
              aria-label="Close notification"
            >
              ×
            </button>
          </div>
        )}
        <header className="app-header">
          <div className="brand">
            <BrandIcon />
            <span className="brand-name">
              DocuChat
              <span className="brand-tagline">AI Document Chat</span>
            </span>
          </div>
        </header>
        <main className="auth-main">
          <div className="auth-hero">
            <div className="hero-badge">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
              </svg>
              AI-Powered Document Intelligence
            </div>
            <h1 className="hero-title">Turn documents into conversations.</h1>
            <p className="hero-subtitle">Search, ask, and get answers from your own files. Upload PDFs and text documents, then chat with them using AI.</p>
            
            <section className="auth-card signin-card">
              <p className="eyebrow">Sign in or sign up</p>
              <h2 className="headline">Continue with Google.</h2>
              <button type="button" className="cta" disabled={authBusy} onClick={signInWithGoogle}>
                {authBusy ? (
                  <span className="cta-loading">
                    <span className="cta-spinner" />
                    Connecting...
                  </span>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                    </svg>
                    Continue with Google
                  </>
                )}
              </button>
              <p className="auth-note">Free to use • No credit card required</p>
            </section>
            {authError ? <p className="auth-error">{authError}</p> : null}
          </div>
        </main>
      </div>
    );
  }

  if (initBusy) {
    return (
      <div className="app">
        <div className="loading-wrap">
          <LoaderScreen message="Finishing sign-in..." />
        </div>
      </div>
    );
  }

  if (initError) {
    return (
      <div className="app">
        <div className="loading-wrap init-error-wrap">
          <div className="init-error-card">
            <div className="init-error-icon">⚠️</div>
            <p className="init-error-msg">{initError}</p>
            <div className="init-error-actions">
              <button type="button" className="btn-outline" onClick={retryInit}>Retry</button>
              <button type="button" className="btn-danger-outline" onClick={signOut}>Sign out</button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (showWelcomeForm) {
    return (
      <div className="app">
        <header className="app-header">
          <div className="brand">
            <BrandIcon />
            <span className="brand-name">
              DocuChat
              <span className="brand-tagline">AI Document Chat</span>
            </span>
          </div>
        </header>

        <main className="app-main onboarding-main">
          {onboardingSubmitting && (
            <div className="onboarding-overlay">
              <LoaderScreen message="Setting up your workspace..." />
            </div>
          )}
          {onboardingSuccess && (
            <div className="onboarding-overlay success-overlay">
              <SuccessScreen message="You're all set!" subMessage="Taking you to your dashboard..." />
            </div>
          )}
          <section className={`onboarding-card ${onboardingSubmitting || onboardingSuccess ? 'card-dimmed' : ''}`}>
            <div className="onboarding-progress">
              <span className="onboarding-progress-dot active" />
              <span className="onboarding-progress-line" />
              <span className="onboarding-progress-dot active" />
              <span className="onboarding-progress-line" />
              <span className="onboarding-progress-dot active" />
            </div>
            <h2 className="onboarding-title">Welcome to DocuChat 👋</h2>
            <p className="onboarding-subtitle">Tell us a little about you — we'll personalize your experience.</p>
            {profileUpdateError && (
              <p className="auth-error onboarding-error">{profileUpdateError}</p>
            )}
            <form className="onboarding-form" onSubmit={handleOnboardingSubmit} noValidate>
              <div className={`onboarding-field ${nameError ? 'field-error' : ''}`}>
                <label className="onboarding-label">Your name</label>
                <input
                  type="text"
                  name="fullName"
                  placeholder="e.g. Alex Chen"
                  aria-invalid={!!nameError}
                  aria-describedby={nameError ? 'name-error' : undefined}
                  onInput={() => setNameError('')}
                  className="onboarding-input"
                />
                {nameError && (
                  <span id="name-error" className="field-error-msg" role="alert">{nameError}</span>
                )}
              </div>

              <div className={`onboarding-field ${roleError ? 'field-error' : ''}`}>
                <label className="onboarding-label">What best describes you?</label>
                <div className="role-grid" role="group" aria-label="Select your role">
                  {ROLE_OPTIONS.map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      className={`role-option ${selectedRole === opt.id ? 'selected' : ''}`}
                      onClick={() => { setSelectedRole(opt.id); setRoleError(''); }}
                    >
                      <span className="role-icon">{opt.icon}</span>
                      <span className="role-label">{opt.label}</span>
                      <span className="role-desc">{opt.desc}</span>
                    </button>
                  ))}
                </div>
                {roleError && (
                  <span className="field-error-msg" role="alert">{roleError}</span>
                )}
              </div>

              <div className="onboarding-field">
                <label className="onboarding-label">Organization <span className="optional">(optional)</span></label>
                <input
                  type="text"
                  name="company"
                  placeholder="e.g. Acme Inc, University"
                  className="onboarding-input"
                />
              </div>

              <button type="submit" className="cta onboarding-cta" disabled={onboardingSubmitting}>
                {onboardingSubmitting ? (
                  <span className="cta-loading">
                    <span className="cta-spinner" />
                    Setting up...
                  </span>
                ) : (
                  'Get started'
                )}
              </button>
            </form>
          </section>
        </main>
      </div>
    );
  }

  if (showWelcomeBack) {
    const readyDocuments = documents.filter((doc) => doc.status === 'ready');
    const hasReadyDocs = readyDocuments.length > 0;
    
    const handlePromptClick = (prompt) => {
      setChatQuestion(prompt);
      setUsedPrompts(prev => new Set([...prev, prompt]));
    };

    return (
      <div className="app app-welcome-back">
        {showBackendWarning && (
          <div className="backend-warning-toast">
            <div className="toast-icon">⏳</div>
            <div className="toast-content">
              <strong>Backend is waking up</strong>
              <p>Free Render instance is spinning up. First request may take 30-60 seconds.</p>
            </div>
            <button 
              type="button" 
              className="toast-close" 
              onClick={() => setShowBackendWarning(false)}
              aria-label="Close notification"
            >
              ×
            </button>
          </div>
        )}
        <header className="app-header">
          <div className="brand">
            <BrandIcon />
            <span className="brand-name">
              DocuChat
              <span className="brand-tagline">AI Document Chat</span>
            </span>
          </div>
          <div className="user-wrap">
            <span className="user-name">{userProfile?.full_name || session.user.email}</span>
            <button type="button" className="btn-danger-outline" onClick={signOut}>
              Sign out
            </button>
          </div>
        </header>

        <main className="app-main">
          {showWelcomeStrip ? (
            <div className="welcome-strip">
              <span>Welcome back, {userProfile?.full_name || 'there'} 👋</span>
              <button
                type="button"
                className="welcome-strip-close"
                aria-label="Close welcome message"
                onClick={() => setShowWelcomeStrip(false)}
              >
                ×
              </button>
            </div>
          ) : null}
          <nav className="workspace-nav" aria-label="Workspace sections">
            <button
              type="button"
              className={`workspace-tab ${activeSection === 'documents' ? 'active' : ''}`}
              onClick={() => setActiveSection('documents')}
            >
              Documents
            </button>
            <button
              type="button"
              className={`workspace-tab ${activeSection === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveSection('chat')}
            >
              Chat
            </button>
            <button
              type="button"
              className={`workspace-tab ${activeSection === 'history' ? 'active' : ''}`}
              onClick={() => setActiveSection('history')}
            >
              History
            </button>
            <button
              type="button"
              className={`workspace-tab ${activeSection === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveSection('settings')}
            >
              Settings
            </button>
          </nav>
          <div className="sections">
            {activeSection === 'documents' ? (
              <section className="section-card">
              <div className="section-header-row">
                <h2>Documents</h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    type="button" 
                    className={`btn-outline btn-compact ${showOrganizationView ? 'active' : ''}`}
                    onClick={() => setShowOrganizationView(!showOrganizationView)}
                  >
                    {showOrganizationView ? '📋 List View' : '📁 Group View'}
                  </button>
                  <button type="button" className="btn-outline btn-compact" onClick={fetchDocuments} disabled={documentsLoading || uploadBusy}>
                    {documentsLoading ? 'Refreshing...' : 'Refresh'}
                  </button>
                  {documents.length > 0 && (
                    <button 
                      type="button" 
                      className="btn-danger-outline btn-compact" 
                      onClick={handleClearAllDocuments} 
                      disabled={clearAllBusy}
                    >
                      {clearAllBusy ? 'Clearing...' : 'Clear All'}
                    </button>
                  )}
                </div>
              </div>
              <p>Upload and manage your PDFs and text files. {showOrganizationView ? 'Browse by groups and categories.' : 'List, select, and delete from one place.'}</p>

              {clearAllError ? <p className="inline-alert" role="alert">{clearAllError}</p> : null}

              {!showOrganizationView && (
                <>
                  <form className="upload-form" onSubmit={handleUploadDocument}>
                    <input type="file" name="file" accept=".pdf,.txt,text/plain,application/pdf" disabled={uploadBusy} />
                    <button type="submit" className="btn-outline" disabled={uploadBusy}>
                      {uploadBusy ? 'Uploading...' : 'Upload'}
                    </button>
                  </form>

                  {uploadDuplicate && (
                    <div className="inline-info" role="status">
                      ℹ️ This file already exists in your library. Showing existing document.
                    </div>
                  )}
                  {uploadError ? <p className="inline-alert" role="alert">{uploadError}</p> : null}
                  {documentsError ? <p className="inline-alert" role="alert">{documentsError}</p> : null}

                  {documentsLoading ? <p className="section-muted">Loading documents...</p> : null}

                  {!documentsLoading && documents.length === 0 ? (
                    <p className="section-muted">No documents yet. Upload your first file to get started.</p>
                  ) : null}

                  {documents.length > 0 ? (
                    <ul className="document-list">
                      {documents.map((doc) => (
                        <li key={doc.id} className="document-item">
                          <div className="document-main">
                            <div className="document-title-row">
                              <span className="file-type-pill">{getFileTypeLabel(doc.filename)}</span>
                              <p className="document-title">{doc.title || doc.filename}</p>
                              <span className={`status-pill status-${doc.status || 'processing'}`}>{doc.status || 'processing'}</span>
                            </div>
                            <p className="document-meta">
                              {doc.filename}
                              {' · '}
                              {formatBytes(doc.file_size)}
                              {doc.created_at ? ` · ${formatDate(doc.created_at)}` : ''}
                            </p>
                          </div>
                          <div className="document-actions">
                            <button
                              type="button"
                              className="btn-primary-inline"
                              onClick={() => {
                                if (doc.status !== 'ready') return;
                                setChatDocumentId(doc.id);
                                setActiveSection('chat');
                              }}
                              disabled={doc.status !== 'ready'}
                            >
                              Use in chat
                            </button>
                            <button
                              type="button"
                              className="btn-outline btn-compact"
                              onClick={() => handleDownloadDocument(doc.id, doc.filename)}
                              title="Download document"
                            >
                              ⬇️ Download
                            </button>
                            <button
                              type="button"
                              className="btn-danger-outline btn-compact"
                              onClick={() => handleDeleteDocument(doc.id)}
                              disabled={deleteBusyId === doc.id}
                            >
                              {deleteBusyId === doc.id ? 'Deleting...' : 'Delete'}
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </>
              )}

              {showOrganizationView && (
                <DocumentOrganization 
                  userId={session?.user?.id}
                  onDocumentSelect={(doc) => {
                    setChatDocumentId(doc.id);
                    setActiveSection('chat');
                  }}
                />
              )}
              </section>
            ) : null}

            {activeSection === 'chat' ? (
              <section className="section-card chat-section">
                <div className="section-header-row">
                  <h2>Chat</h2>
                  {conversationMessages.length > 0 && (
                    <button 
                      type="button" 
                      className="btn-outline btn-compact" 
                      onClick={handleNewConversation}
                    >
                      New Conversation
                    </button>
                  )}
                </div>
                <p>Ask questions about your documents. Your conversation is saved automatically.</p>

                {/* Document Scope Selector */}
                <div className="chat-controls">
                  <label className="chat-label" htmlFor="chat-document-scope">
                    Document scope
                  </label>
                  <select
                    id="chat-document-scope"
                    className="chat-select compact"
                    value={chatDocumentId}
                    onChange={(event) => setChatDocumentId(event.target.value)}
                    disabled={chatBusy || !hasReadyDocs}
                  >
                    <option value="all">All ready documents</option>
                    {readyDocuments.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.title || doc.filename}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Conversation Area */}
                <div className="conversation-container">
                  {conversationMessages.length === 0 ? (
                    <div className="conversation-empty">
                      <div className="empty-icon">💬</div>
                      <h3>Start a conversation</h3>
                      <p>Ask a question about your documents to begin.</p>
                      
                      {/* Suggestion chips when empty */}
                      <div className="chat-prompts">
                        {currentPrompts.slice(0, 3).map((prompt) => (
                          <button
                            key={prompt}
                            type="button"
                            className="prompt-chip"
                            onClick={() => handlePromptClick(prompt)}
                            disabled={chatBusy || !hasReadyDocs}
                          >
                            {prompt}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="conversation-messages">
                      {conversationMessages.map((msg) => (
                        <div key={msg.id} className={`conversation-message ${msg.type}`}>
                          {msg.type === 'user' ? (
                            <div className="message-bubble user-bubble">
                              <div className="message-content">{msg.content}</div>
                            </div>
                          ) : (
                            <div className="message-bubble assistant-bubble">
                              <div className="message-content markdown-content">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                              </div>
                              {msg.sources && msg.sources.length > 0 && (
                                <div className="message-sources-inline">
                                  <strong>Sources:</strong>{' '}
                                  {msg.sources.map((source, idx) => (
                                    <span key={idx} className="source-tag">
                                      {source.filename}
                                      {source.page_start && ` (p.${source.page_start})`}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                      {chatBusy && (
                        <div className="conversation-message assistant">
                          <div className="message-bubble assistant-bubble typing">
                            <div className="typing-indicator">
                              <span></span>
                              <span></span>
                              <span></span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Input Area */}
                <div className="chat-input-area">
                  {chatError && <p className="inline-alert" role="alert">{chatError}</p>}
                  
                  {!hasReadyDocs && (
                    <p className="inline-alert" role="alert">
                      No ready documents yet. Upload a file and wait until its status is ready.
                    </p>
                  )}

                  {/* Suggestion chips above input */}
                  {conversationMessages.length > 0 && (
                    <div className="chat-prompts compact">
                      {currentPrompts.slice(0, 3).map((prompt) => (
                        <button
                          key={prompt}
                          type="button"
                          className="prompt-chip small"
                          onClick={() => handlePromptClick(prompt)}
                          disabled={chatBusy || !hasReadyDocs}
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  )}

                  <form className="chat-input-form" onSubmit={handleChatSubmit}>
                    <textarea
                      id="chat-question"
                      className="chat-input"
                      rows={2}
                      value={chatQuestion}
                      onChange={(event) => setChatQuestion(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' && !event.shiftKey) {
                          event.preventDefault();
                          handleChatSubmit(event);
                        }
                      }}
                      placeholder="Ask a question... (Press Enter to send, Shift+Enter for new line)"
                      disabled={chatBusy || !hasReadyDocs}
                    />
                    <button 
                      type="submit" 
                      className="chat-send-btn" 
                      disabled={chatBusy || !chatQuestion.trim() || !hasReadyDocs}
                      aria-label="Send message"
                    >
                      {chatBusy ? (
                        <span className="btn-spinner"></span>
                      ) : (
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z"/>
                        </svg>
                      )}
                    </button>
                  </form>
                </div>
              </section>
            ) : null}

            {activeSection === 'history' ? (
              <section className="section-card">
                <div className="section-header-row">
                  <h2>Chat History</h2>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button 
                      type="button" 
                      className="btn-outline btn-compact" 
                      onClick={handleExportHistory}
                      disabled={chatSessions.length === 0}
                    >
                      Export
                    </button>
                    {chatSessions.length > 0 && (
                      <button 
                        type="button" 
                        className="btn-danger-outline btn-compact" 
                        onClick={handleClearAllHistory}
                      >
                        Clear All
                      </button>
                    )}
                  </div>
                </div>
                <p>View and manage your previous conversations with documents.</p>

                {/* Search Bar */}
                <div className="history-search">
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      handleSearchHistory(e.target.value);
                    }}
                  />
                  {searchLoading && <span className="search-loading">Searching...</span>}
                </div>

                {/* Search Results */}
                {searchQuery && searchResults.length > 0 && (
                  <div className="search-results">
                    <h3>Search Results ({searchResults.length})</h3>
                    <ul className="message-list">
                      {searchResults.map((msg) => (
                        <li key={msg.id} className="message-item">
                          <div className="message-q">
                            <strong>Q:</strong> {msg.question}
                          </div>
                          <div className="message-a">
                            <strong>A:</strong> {msg.answer.substring(0, 200)}...
                          </div>
                          <div className="message-meta">
                            {formatDate(msg.created_at)}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Sessions List */}
                {!searchQuery && (
                  <div className="history-content">
                    {sessionsLoading && <p className="section-muted">Loading sessions...</p>}
                    {sessionsError && <p className="inline-alert">{sessionsError}</p>}

                    {!sessionsLoading && chatSessions.length === 0 && (
                      <div className="coming-soon-card">
                        <div className="coming-soon-icon">💬</div>
                        <h3>No Chat History Yet</h3>
                        <p>Start a conversation in the Chat tab to see your history here.</p>
                      </div>
                    )}

                    {chatSessions.length > 0 && (
                      <div className="sessions-grid">
                        <div className="sessions-list">
                          <h3>Conversations ({chatSessions.length})</h3>
                          <ul className="session-list">
                            {chatSessions.map((sess) => (
                              <li 
                                key={sess.id} 
                                className={`session-item ${selectedSession === sess.id ? 'active' : ''}`}
                                onClick={() => fetchSessionDetail(sess.id)}
                              >
                                <div className="session-title">
                                  {sess.title || 'Untitled Conversation'}
                                </div>
                                <div className="session-meta">
                                  {sess.message_count} message{sess.message_count !== 1 ? 's' : ''} · {formatDate(sess.updated_at)}
                                </div>
                                {sess.last_message && (
                                  <div className="session-preview">
                                    {sess.last_message.substring(0, 60)}...
                                  </div>
                                )}
                                <div className="session-actions">
                                  <button
                                    type="button"
                                    className="btn-primary-inline btn-compact"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleResumeSession(sess.id);
                                    }}
                                  >
                                    Resume
                                  </button>
                                  <button
                                    type="button"
                                    className="btn-danger-outline btn-compact"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleDeleteSession(sess.id);
                                    }}
                                  >
                                    Delete
                                  </button>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {selectedSession && sessionDetail && (
                          <div className="session-detail">
                            {sessionDetailLoading ? (
                              <p className="section-muted">Loading messages...</p>
                            ) : (
                              <>
                                <div className="detail-header">
                                  <h3>{sessionDetail.title || 'Conversation'}</h3>
                                  <button
                                    type="button"
                                    className="btn-outline btn-compact"
                                    onClick={() => {
                                      setSelectedSession(null);
                                      setSessionDetail(null);
                                    }}
                                  >
                                    Close
                                  </button>
                                </div>
                                <div className="messages-container">
                                  {sessionDetail.messages.map((msg) => (
                                    <div key={msg.id} className="message-pair">
                                      <div className="message-bubble user-message">
                                        <div className="message-label">You asked:</div>
                                        <div className="message-text">{msg.question}</div>
                                        <div className="message-time">{formatDate(msg.created_at)}</div>
                                      </div>
                                      <div className="message-bubble assistant-message">
                                        <div className="message-label">DocuChat:</div>
                                        <div className="message-text markdown-content">
                                          <ReactMarkdown>{msg.answer}</ReactMarkdown>
                                        </div>
                                        {msg.sources && msg.sources.length > 0 && (
                                          <div className="message-sources">
                                            <strong>Sources:</strong> {msg.sources.map(s => s.filename).join(', ')}
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </section>
            ) : null}

            {activeSection === 'settings' ? (
              <section className="section-card">
                <h2>Settings</h2>
                <p>Manage your account preferences and application settings.</p>
                
                <div className="settings-grid">
                  <div className="settings-section">
                    <h3>Profile</h3>
                    <div className="settings-item">
                      <label>Full Name</label>
                      <input 
                        type="text" 
                        className="settings-input" 
                        value={userProfile?.full_name || ''} 
                        disabled 
                      />
                    </div>
                    <div className="settings-item">
                      <label>Email</label>
                      <input 
                        type="email" 
                        className="settings-input" 
                        value={session.user.email || ''} 
                        disabled 
                      />
                    </div>
                    <div className="settings-item">
                      <label>Role</label>
                      <input 
                        type="text" 
                        className="settings-input" 
                        value={userProfile?.role || ''} 
                        disabled 
                      />
                    </div>
                    <div className="settings-item">
                      <label>Organization</label>
                      <input 
                        type="text" 
                        className="settings-input" 
                        value={userProfile?.company || 'Not specified'} 
                        disabled 
                      />
                    </div>
                  </div>

                  <div className="settings-section">
                    <h3>Preferences</h3>
                    <div className="coming-soon-card compact">
                      <p>Additional settings coming soon:</p>
                      <ul className="feature-list">
                        <li>Theme customization (Light/Dark mode)</li>
                        <li>Default document scope for chat</li>
                        <li>Language preferences</li>
                        <li>Notification settings</li>
                        <li>Export data options</li>
                      </ul>
                    </div>
                  </div>

                  <div className="settings-section">
                    <h3>Account</h3>
                    <div className="settings-item">
                      <label>Account Status</label>
                      <div className="status-badge active">Active</div>
                    </div>
                    <div className="settings-item">
                      <label>Member Since</label>
                      <input 
                        type="text" 
                        className="settings-input" 
                        value={userProfile?.created_at ? new Date(userProfile.created_at).toLocaleDateString() : 'N/A'} 
                        disabled 
                      />
                    </div>
                    <div className="settings-item">
                      <button type="button" className="btn-danger-outline" onClick={signOut}>
                        Sign Out
                      </button>
                    </div>
                  </div>
                </div>
              </section>
            ) : null}

          </div>
        </main>
      </div>
    );
  }

  return null;
}

export default App;
