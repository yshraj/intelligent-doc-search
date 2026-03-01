import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import './TagManager.css';

export default function TagManager({ documentId, onTagsChange }) {
  const [tags, setTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddTag, setShowAddTag] = useState(false);
  const [newTag, setNewTag] = useState({
    tag_name: '',
    tag_category: 'custom',
  });

  useEffect(() => {
    if (documentId) {
      fetchTags();
    }
  }, [documentId]);

  const fetchTags = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await fetch(`http://localhost:8000/groups/documents/${documentId}/tags`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTags(data);
        onTagsChange?.(data);
      }
    } catch (error) {
      console.error('Error fetching tags:', error);
    } finally {
      setLoading(false);
    }
  };

  const addTag = async () => {
    if (!newTag.tag_name.trim()) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await fetch(`http://localhost:8000/groups/documents/${documentId}/tags`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tag_name: newTag.tag_name.trim(),
          tag_category: newTag.tag_category,
          confidence_score: 1.0,
          auto_generated: false,
        }),
      });

      if (response.ok) {
        setNewTag({ tag_name: '', tag_category: 'custom' });
        setShowAddTag(false);
        fetchTags();
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to add tag');
      }
    } catch (error) {
      console.error('Error adding tag:', error);
      alert('Failed to add tag');
    }
  };

  const removeTag = async (tagId) => {
    if (!confirm('Remove this tag?')) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const response = await fetch(`http://localhost:8000/groups/documents/${documentId}/tags/${tagId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      });

      if (response.ok) {
        fetchTags();
      }
    } catch (error) {
      console.error('Error removing tag:', error);
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      type: '#2196F3',
      topic: '#4CAF50',
      department: '#FF9800',
      sensitivity: '#F44336',
      time_period: '#9C27B0',
      status: '#607D8B',
      custom: '#795548',
    };
    return colors[category] || '#999';
  };

  const getCategoryIcon = (category) => {
    const icons = {
      type: '📄',
      topic: '🏷️',
      department: '🏢',
      sensitivity: '🔒',
      time_period: '📅',
      status: '📊',
      custom: '⭐',
    };
    return icons[category] || '🏷️';
  };

  const getConfidenceLabel = (score) => {
    if (score >= 0.9) return 'High';
    if (score >= 0.7) return 'Medium';
    return 'Low';
  };

  if (loading) {
    return <div className="tag-manager-loading">Loading tags...</div>;
  }

  return (
    <div className="tag-manager">
      <div className="tag-manager-header">
        <h4>🏷️ Tags</h4>
        <button className="add-tag-btn" onClick={() => setShowAddTag(!showAddTag)}>
          {showAddTag ? '✕' : '+ Add Tag'}
        </button>
      </div>

      {showAddTag && (
        <div className="add-tag-form">
          <input
            type="text"
            placeholder="Tag name"
            value={newTag.tag_name}
            onChange={(e) => setNewTag({ ...newTag, tag_name: e.target.value })}
            onKeyPress={(e) => e.key === 'Enter' && addTag()}
          />
          <select
            value={newTag.tag_category}
            onChange={(e) => setNewTag({ ...newTag, tag_category: e.target.value })}
          >
            <option value="custom">Custom</option>
            <option value="type">Type</option>
            <option value="topic">Topic</option>
            <option value="department">Department</option>
            <option value="sensitivity">Sensitivity</option>
            <option value="time_period">Time Period</option>
            <option value="status">Status</option>
          </select>
          <button onClick={addTag}>Add</button>
        </div>
      )}

      <div className="tags-list">
        {tags.length === 0 ? (
          <div className="no-tags">
            <p>No tags yet</p>
            <p className="hint">Add tags to organize this document</p>
          </div>
        ) : (
          tags.map(tag => (
            <div
              key={tag.id}
              className="tag-item"
              style={{ borderLeftColor: getCategoryColor(tag.tag_category) }}
            >
              <div className="tag-content">
                <span className="tag-icon">{getCategoryIcon(tag.tag_category)}</span>
                <div className="tag-info">
                  <div className="tag-name">{tag.tag_name}</div>
                  <div className="tag-meta">
                    <span className="tag-category">{tag.tag_category}</span>
                    {tag.auto_generated && (
                      <>
                        <span className="tag-separator">•</span>
                        <span className="tag-confidence">
                          {getConfidenceLabel(tag.confidence_score)} confidence
                        </span>
                      </>
                    )}
                    {!tag.auto_generated && (
                      <>
                        <span className="tag-separator">•</span>
                        <span className="tag-manual">Manual</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <button
                className="remove-tag-btn"
                onClick={() => removeTag(tag.id)}
                title="Remove tag"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
