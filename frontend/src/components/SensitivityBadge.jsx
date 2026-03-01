import './SensitivityBadge.css';

export default function SensitivityBadge({ level, onClick }) {
  const getConfig = (level) => {
    const configs = {
      public: {
        color: '#4CAF50',
        icon: '🌐',
        label: 'Public',
        description: 'Publicly accessible document',
      },
      internal: {
        color: '#2196F3',
        icon: '🏢',
        label: 'Internal',
        description: 'Internal use only',
      },
      confidential: {
        color: '#F44336',
        icon: '🔒',
        label: 'Confidential',
        description: 'Confidential - restricted access',
      },
      anonymous: {
        color: '#9E9E9E',
        icon: '❓',
        label: 'Anonymous',
        description: 'Missing metadata - needs review',
      },
    };
    return configs[level] || configs.internal;
  };

  const config = getConfig(level);

  return (
    <div
      className="sensitivity-badge"
      style={{ background: config.color }}
      onClick={onClick}
      title={config.description}
    >
      <span className="badge-icon">{config.icon}</span>
      <span className="badge-label">{config.label}</span>
    </div>
  );
}
