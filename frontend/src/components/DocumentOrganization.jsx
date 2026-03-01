import { useState, useEffect, useCallback, useRef } from 'react';
import { API_URL, supabase } from '../lib/supabase';
import './DocumentOrganization.css';

export default function DocumentOrganization({ userId, onDocumentSelect }) {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState(new Set());
  const [downloadingDocId, setDownloadingDocId] = useState('');
  
  // Cache for group documents - prevents unnecessary API calls
  const documentsCache = useRef(new Map());
  const [loadingGroups, setLoadingGroups] = useState(new Set());
  
  // Prevent multiple simultaneous fetches
  const fetchingRef = useRef(false);

  useEffect(() => {
    if (userId) {
      fetchGroups();
    }
  }, [userId]);

  const handleDownloadDocument = useCallback(async (documentId, filename) => {
    if (downloadingDocId) return; // Prevent multiple downloads
    
    setDownloadingDocId(documentId);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

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
      console.error('Download failed:', error);
      alert('Failed to download document. Please try again.');
    } finally {
      setDownloadingDocId('');
    }
  }, [downloadingDocId]);

  const fetchGroups = useCallback(async () => {
    if (fetchingRef.current) return; // Prevent duplicate calls
    
    fetchingRef.current = true;
    setLoading(true);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await fetch(`${API_URL}/groups`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setGroups(data);
      } else {
        console.error('Failed to fetch groups:', response.status);
      }
    } catch (error) {
      console.error('Error fetching groups:', error);
    } finally {
      setLoading(false);
      fetchingRef.current = false;
    }
  }, []);

  const fetchGroupDocuments = useCallback(async (groupId) => {
    // Check cache first
    if (documentsCache.current.has(groupId)) {
      return documentsCache.current.get(groupId);
    }

    // Prevent duplicate fetches for the same group
    if (loadingGroups.has(groupId)) {
      return null;
    }

    setLoadingGroups(prev => new Set(prev).add(groupId));

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return null;

      const response = await fetch(`${API_URL}/groups/${groupId}/documents`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Cache the result
        documentsCache.current.set(groupId, data);
        return data;
      } else {
        console.error('Failed to fetch group documents:', response.status);
        return null;
      }
    } catch (error) {
      console.error('Error fetching group documents:', error);
      return null;
    } finally {
      setLoadingGroups(prev => {
        const newSet = new Set(prev);
        newSet.delete(groupId);
        return newSet;
      });
    }
  }, [loadingGroups]);

  const handleGroupClick = useCallback(async (group) => {
    const groupId = group.id;
    const isExpanded = expandedGroups.has(groupId);

    if (isExpanded) {
      // Collapse - just remove from expanded set
      setExpandedGroups(prev => {
        const newSet = new Set(prev);
        newSet.delete(groupId);
        return newSet;
      });
    } else {
      // Expand - add to expanded set and fetch documents if not cached
      setExpandedGroups(prev => new Set(prev).add(groupId));
      
      // Fetch documents if not in cache
      if (!documentsCache.current.has(groupId)) {
        await fetchGroupDocuments(groupId);
      }
    }
  }, [expandedGroups, fetchGroupDocuments]);

  const handleRefresh = useCallback(() => {
    // Clear cache on refresh
    documentsCache.current.clear();
    setExpandedGroups(new Set());
    fetchGroups();
  }, [fetchGroups]);

  const groupByType = useCallback(() => {
    const grouped = {};
    groups.forEach(group => {
      if (!grouped[group.group_type]) {
        grouped[group.group_type] = [];
      }
      grouped[group.group_type].push(group);
    });
    return grouped;
  }, [groups]);

  const getGroupIcon = (groupType) => {
    const icons = {
      type_based: '📄',
      topic_based: '🏷️',
      time_based: '📅',
      department_based: '🏢',
      custom: '⭐',
    };
    return icons[groupType] || '📁';
  };

  const getGroupTypeLabel = (groupType) => {
    const labels = {
      type_based: 'By Type',
      topic_based: 'By Topic',
      time_based: 'By Time',
      department_based: 'By Department',
      custom: 'Custom',
    };
    return labels[groupType] || groupType;
  };

  if (loading) {
    return <div className="doc-org-loading">Loading groups...</div>;
  }

  const groupedByType = groupByType();

  return (
    <div className="document-organization">
      <div className="doc-org-header">
        <h3>Document Organization</h3>
        <button 
          className="refresh-btn" 
          onClick={handleRefresh}
          disabled={loading}
          title="Refresh groups"
        >
          ↻
        </button>
      </div>

      <div className="doc-org-content">
        <div className="groups-panel">
          {Object.entries(groupedByType).map(([type, typeGroups]) => (
            <div key={type} className="group-type-section">
              <div className="group-type-header">
                {getGroupIcon(type)} {getGroupTypeLabel(type)}
              </div>
              
              {typeGroups.map(group => {
                const isExpanded = expandedGroups.has(group.id);
                const isLoading = loadingGroups.has(group.id);
                const cachedDocs = documentsCache.current.get(group.id) || [];
                
                return (
                  <div key={group.id} className="group-item">
                    <div
                      className={`group-name ${isExpanded ? 'expanded' : ''}`}
                      onClick={() => handleGroupClick(group)}
                    >
                      <span className="group-icon">
                        {isExpanded ? '▼' : '▶'}
                      </span>
                      <span className="group-label">{group.group_name}</span>
                      <span className="doc-count">{group.document_count}</span>
                    </div>
                    
                    {isExpanded && (
                      <div className="group-documents">
                        {isLoading ? (
                          <div className="no-documents">Loading documents...</div>
                        ) : cachedDocs.length === 0 ? (
                          <div className="no-documents">No documents</div>
                        ) : (
                          cachedDocs.map(doc => (
                            <div key={doc.id} className="doc-item-wrapper">
                              <div
                                className="doc-item"
                                onClick={() => onDocumentSelect?.(doc)}
                              >
                                <span className="doc-icon">📄</span>
                                <span className="doc-name">{doc.filename}</span>
                              </div>
                              <button
                                className="doc-download-btn"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDownloadDocument(doc.id, doc.filename);
                                }}
                                disabled={downloadingDocId === doc.id}
                                title={downloadingDocId === doc.id ? "Downloading..." : "Download"}
                              >
                                {downloadingDocId === doc.id ? '...' : '↓'}
                              </button>
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          {groups.length === 0 && (
            <div className="no-groups">
              <p>No groups yet</p>
              <p className="hint">Upload documents to create groups automatically</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
