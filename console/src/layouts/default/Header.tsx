/**
 * Default Header Component
 *
 * 顶部导航栏：
 * - Logo + 项目标题
 * - 侧边栏折叠按钮
 * - 语言切换和主题切换
 * - 用户信息下拉菜单
 * - 快捷操作
 */
import { Layout, Avatar, Dropdown, Space, Button, Tooltip } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import LanguageSwitcher from '../../components/LanguageSwitcher';
import ThemeToggleButton from '../../components/ThemeToggleButton';
import { useTheme } from '../../contexts/ThemeContext';
import styles from './index.module.less';

const { Header: AntHeader } = Layout;

// ============================================================================
// Types
// ============================================================================

interface DefaultHeaderProps {
  onToggleCollapsed: () => void;
  collapsed: boolean;
}

// ============================================================================
// Component
// ============================================================================

export default function DefaultHeader({
  onToggleCollapsed,
  collapsed,
}: DefaultHeaderProps) {
  const navigate = useNavigate();
  const { isDark } = useTheme();

  // 模拟用户数据（实际应从 Auth Context 获取）
  const currentUser = {
    name: 'Admin User',
    email: 'admin@copaw.io',
    avatar: null,
  };

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '账户设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
      onClick: () => {
        // TODO: 调用登出 API
        navigate('/login');
      },
    },
  ];

  return (
    <AntHeader className={styles.header}>
      <div className={styles.headerLeft}>
        <Tooltip title={collapsed ? '展开侧边栏' : '收起侧边栏'}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={onToggleCollapsed}
            className={styles.triggerButton}
          />
        </Tooltip>
        <div className={styles.logo}>
          <DashboardOutlined className={styles.logoIcon} />
          {!collapsed && <span className={styles.logoText}>CoPaw Enterprise</span>}
        </div>
      </div>

      <div className={styles.headerRight}>
        {/* 语言切换 */}
        <LanguageSwitcher />
        
        {/* 主题切换 */}
        <ThemeToggleButton />
        
        {/* 用户菜单 */}
        <Dropdown
          menu={{ items: userMenuItems }}
          placement="bottomRight"
          arrow
        >
          <Space className={styles.userMenu}>
            <Avatar
              size="default"
              src={currentUser.avatar}
              icon={<UserOutlined />}
            />
            <span className={styles.userName}>{currentUser.name}</span>
          </Space>
        </Dropdown>
      </div>
    </AntHeader>
  );
}
