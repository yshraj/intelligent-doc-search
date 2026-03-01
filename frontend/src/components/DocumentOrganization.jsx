import { useState, useEffect } from 'react';
import { API_URL, supabase } from '../lib/supabase';
import './DocumentOrganization.css';

export default function DocumentOrganization({ userId, onDocumentSelect }) {
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [groupDocuments, setGroupDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState(new Set());

  useEffect(() => {
    if (userId) {
      fetchGroups();
    }
  }, [userId]);

  const fetchGroups = async () => {
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
      }
    } catch (error) {
      console.error('Error fetching groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGroupDocuments = async (groupId) => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await fetch(`${API_URL}/groups/${groupId}/documents`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setGroupDocuments(data);
      }
    } catch (error) {
      console.error('Error fetching group documents:', error);
    }
  };

  const handleGroupClick = (group) => {
    setSelectedGroup(group);
    fetchGroupDocuments(group.id);
    
    // Toggle expand/collapse
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(group.id)) {
      newExpanded.delete(group.id);
    } else {
      newExpanded.add(group.id);
    }
    setExpandedGroups(newExpanded);
  };

  const groupByType = () => {
    const grouped = {};
    groups.forEach(group => {
      if (!grouped[group.group_type]) {
        grouped[group.group_type] = [];
      }
      grouped[group.group_type].push(group);
    });
    return grouped;
  };

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
        <h3>📁 Document Organization</h3>
        <button className="refresh-btn" onClick={fetchGroups}>
          🔄
        </button>
      </div>

      <div className="doc-org-content">
        <div className="groups-panel">
          {Object.entries(groupedByType).map(([type, typeGroups]) => (
            <div key={type} className="group-type-section">
              <div className="group-type-header">
                {getGroupIcon(type)} {getGroupTypeLabel(type)}
              </div>
              
              {typeGroups.map(group => (
                <div key={group.id} className="group-item">
                  <div
                    className={`group-name ${selectedGroup?.id === group.id ? 'selected' : ''}`}
                    onClick={() => handleGroupClick(group)}
                  >
                    <span className="group-icon">
                      {expandedGroups.has(group.id) ? '▼' : '▶'}
                    </span>
                    <span className="group-label">{group.group_name}</span>
                    <span className="doc-count">{group.document_count}</span>
                  </div>
                  
                  {expandedGroups.has(group.id) && selectedGroup?.id === group.id && (
                    <div className="group-documents">
                      {groupDocuments.length === 0 ? (
                        <div className="no-documents">No documents</div>
                      ) : (
                        groupDocuments.map(doc => (
                          <div
                            key={doc.id}
                            className="doc-item"
                            onClick={() => onDocumentSelect?.(doc)}
                          >
                            <span className="doc-icon">📄</span>
                            <span className="doc-name">{doc.filename}</span>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))}
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
