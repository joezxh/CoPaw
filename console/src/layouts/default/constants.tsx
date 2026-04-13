/**
 * Default Layout Menu Configuration
 *
 * 菜单配置 - 每个菜单项包含权限码
 * 用于权限过滤和菜单渲染
 */
import {
  SparkChatTabFill,
  SparkWifiLine,
  SparkUserGroupLine,
  SparkDateLine,
  SparkVoiceChat01Line,
  SparkMagicWandLine,
  SparkToolLine,
  SparkMcpMcpLine,
  SparkLocalFileLine,
  SparkModePlazaLine,
  SparkInternetLine,
  SparkModifyLine,
  SparkBrowseLine,
  SparkDataLine,
  SparkMicLine,
  SparkSearchUserLine,
  SparkOtherLine,
  SparkAgentLine,
} from '@agentscope-ai/icons';

// ============================================================================
// Types
// ============================================================================

export interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  permission?: string;  // 权限码
  children?: MenuItem[];
}

// ============================================================================
// Menu Configuration
// ============================================================================

export const menuConfig: MenuItem[] = [
  // ── 聊天 ────────────────────────────────────────────────────────
  {
    key: 'chat',
    label: 'menu.chat',
    icon: <SparkChatTabFill size={18} />,
    path: '/chat',
    permission: 'chat:access',
  },

  // ── 控制台 ──────────────────────────────────────────────────────
  {
    key: 'control-group',
    label: 'menu.control',
    icon: <SparkWifiLine size={18} />,
    permission: 'channel:read',
    children: [
      {
        key: 'channels',
        label: 'menu.channels',
        icon: <SparkWifiLine size={18} />,
        path: '/channels',
        permission: 'channel:read',
      },
      {
        key: 'sessions',
        label: 'menu.sessions',
        icon: <SparkUserGroupLine size={18} />,
        path: '/sessions',
        permission: 'session:read',
      },
      {
        key: 'cron-jobs',
        label: 'menu.cronJobs',
        icon: <SparkDateLine size={18} />,
        path: '/cron-jobs',
        permission: 'cronjob:read',
      },
      {
        key: 'heartbeat',
        label: 'menu.heartbeat',
        icon: <SparkVoiceChat01Line size={18} />,
        path: '/heartbeat',
        permission: 'heartbeat:read',
      },
    ],
  },

  // ── Agent 管理 ──────────────────────────────────────────────────
  {
    key: 'agent-group',
    label: 'menu.agentManagement',
    icon: <SparkMagicWandLine size={18} />,
    permission: 'agent:config:read',
    children: [
      {
        key: 'agent-config',
        label: 'menu.agentConfig',
        icon: <SparkModifyLine size={18} />,
        path: '/agent-config',
        permission: 'agent:config:read',
      },
      {
        key: 'skills',
        label: 'menu.skills',
        icon: <SparkMagicWandLine size={18} />,
        path: '/skills',
        permission: 'agent:skill:read',
      },
      {
        key: 'tools',
        label: 'menu.tools',
        icon: <SparkToolLine size={18} />,
        path: '/tools',
        permission: 'tool:read',
      },
      {
        key: 'mcp',
        label: 'menu.mcp',
        icon: <SparkMcpMcpLine size={18} />,
        path: '/mcp',
        permission: 'mcp:read',
      },
      {
        key: 'workspace',
        label: 'menu.workspace',
        icon: <SparkLocalFileLine size={18} />,
        path: '/workspace',
        permission: 'workspace:read',
      },
    ],
  },

  // ── 设置 ────────────────────────────────────────────────────────
  {
    key: 'settings-group',
    label: 'menu.settings',
    icon: <SparkModifyLine size={18} />,
    permission: 'model:read',
    children: [
      {
        key: 'skill-pool',
        label: 'menu.skillPool',
        icon: <SparkMagicWandLine size={18} />,
        path: '/skill-pool',
        permission: 'skill:pool:read',
      },
      {
        key: 'models',
        label: 'menu.models',
        icon: <SparkModePlazaLine size={18} />,
        path: '/models',
        permission: 'model:read',
      },
      {
        key: 'environments',
        label: 'menu.environments',
        icon: <SparkInternetLine size={18} />,
        path: '/environments',
        permission: 'environment:read',
      },
      {
        key: 'agents',
        label: 'menu.agents',
        icon: <SparkAgentLine size={18} />,
        path: '/agents',
        permission: 'agent:config:read',
      },
      {
        key: 'security',
        label: 'menu.security',
        icon: <SparkBrowseLine size={18} />,
        path: '/security',
        permission: 'security:read',
      },
      {
        key: 'token-usage',
        label: 'menu.tokenUsage',
        icon: <SparkDataLine size={18} />,
        path: '/token-usage',
        permission: 'token:usage:read',
      },
      {
        key: 'voice-transcription',
        label: 'menu.voiceTranscription',
        icon: <SparkMicLine size={18} />,
        path: '/voice-transcription',
        permission: 'voice:transcription:read',
      },
    ],
  },

  // ── 企业管理 ────────────────────────────────────────────────────
  {
    key: 'enterprise-group',
    label: 'menu.enterprise',
    icon: <SparkBrowseLine size={18} />,
    permission: 'user:read',
    children: [
      {
        key: 'enterprise-users',
        label: 'menu.enterpriseUsers',
        icon: <SparkSearchUserLine size={18} />,
        path: '/enterprise/users',
        permission: 'user:read',
      },
      {
        key: 'enterprise-permissions',
        label: 'menu.enterprisePermissions',
        icon: <SparkBrowseLine size={18} />,
        path: '/enterprise/permissions',
        permission: 'role:read',
      },
      {
        key: 'enterprise-orgs',
        label: 'menu.enterpriseOrgs',
        icon: <SparkUserGroupLine size={18} />,
        path: '/enterprise/organizations',
        permission: 'org:read',
      },
      {
        key: 'enterprise-workflows',
        label: 'menu.enterpriseWorkflows',
        icon: <SparkMagicWandLine size={18} />,
        path: '/enterprise/workflows',
        permission: 'workflow:read',
      },
      {
        key: 'enterprise-tasks',
        label: 'menu.enterpriseTasks',
        icon: <SparkDateLine size={18} />,
        path: '/enterprise/tasks',
        permission: 'task:read',
      },
      {
        key: 'dlp-rules',
        label: 'menu.dlpRules',
        icon: <SparkOtherLine size={18} />,
        path: '/enterprise/dlp-rules',
        permission: 'dlp:rule:read',
      },
      {
        key: 'alert-rules',
        label: 'menu.alertRules',
        icon: <SparkVoiceChat01Line size={18} />,
        path: '/enterprise/alert-rules',
        permission: 'alert:rule:read',
      },
      {
        key: 'dify-connectors',
        label: 'menu.difyConnectors',
        icon: <SparkMcpMcpLine size={18} />,
        path: '/enterprise/dify-connectors',
        permission: 'dify:connector:read',
      },
      {
        key: 'enterprise-audit',
        label: 'menu.enterpriseAudit',
        icon: <SparkBrowseLine size={18} />,
        path: '/enterprise/audit',
        permission: 'audit:log:read',
      },
    ],
  },
];

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * 获取菜单项的路径映射
 */
export const menuPathMap: Record<string, string> = {};
menuConfig.forEach((item) => {
  if (item.path) {
    menuPathMap[item.key] = item.path;
  }
  if (item.children) {
    item.children.forEach((child) => {
      if (child.path) {
        menuPathMap[child.key] = child.path;
      }
    });
  }
});

/**
 * 获取菜单项的标签映射
 */
export const menuLabelMap: Record<string, string> = {};
menuConfig.forEach((item) => {
  menuLabelMap[item.key] = item.label;
  if (item.children) {
    item.children.forEach((child) => {
      menuLabelMap[child.key] = child.label;
    });
  }
});
