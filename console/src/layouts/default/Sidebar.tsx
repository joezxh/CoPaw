/**
 * Default Sidebar Component
 *
 * 企业版侧边栏 - 带权限控制
 * - 顶部集成智能体切换器
 * - 手风琴菜单（同时只保持一个子菜单展开）
 * - 根据用户权限过滤菜单项
 * - 支持折叠/展开
 * - 菜单结构与个人版保持一致
 */
import { useState, useMemo, useEffect } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { usePermissions } from '../../hooks/usePermissions';
import { useTheme } from '../../contexts/ThemeContext';
import AgentSelector from '../../components/AgentSelector';
import { menuConfig } from './constants';
import type { MenuItem } from './constants';
import styles from './index.module.less';

const { Sider } = Layout;

// ============================================================================
// Types
// ============================================================================

interface DefaultSidebarProps {
  selectedKey: string;
  collapsed: boolean;
}

// ============================================================================
// Component
// ============================================================================

export default function DefaultSidebar({
  selectedKey,
  collapsed,
}: DefaultSidebarProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { hasPermission, loading } = usePermissions();
  const { isDark } = useTheme();
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  // 根据当前路径设置展开的菜单
  useEffect(() => {
    const currentMenu = menuConfig.find(
      (item) => item.path === location.pathname
    );

    if (currentMenu) {
      setOpenKeys([]);
    } else {
      // 查找父菜单
      const parentMenu = menuConfig.find(
        (item) =>
          item.children?.some((child) => child.path === location.pathname)
      );
      if (parentMenu) {
        setOpenKeys([parentMenu.key]);
      }
    }
  }, [location.pathname]);

  // 过滤有权限的菜单项
  const filteredMenu = useMemo(() => {
    return filterMenuByPermission(menuConfig, hasPermission);
  }, [hasPermission]);

  // 将 MenuItem 转换为 Ant Design Menu 格式
  const menuItems = useMemo(() => {
    return convertToMenuItems(filteredMenu, t);
  }, [filteredMenu, t]);

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    const path = findMenuPath(menuConfig, key);
    if (path) {
      navigate(path);
    }
  };

  // 手风琴模式：只保持一个子菜单展开
  const handleOpenChange = (keys: string[]) => {
    if (keys.length === 0) {
      setOpenKeys([]);
    } else {
      // 只保留最后一个展开的菜单
      setOpenKeys([keys[keys.length - 1]]);
    }
  };

  // 加载中
  if (loading) {
    return (
      <Sider
        width={256}
        collapsed={collapsed}
        className={`${styles.sider}${isDark ? ` ${styles.siderDark}` : ''}`}
        trigger={null}
      >
        <div className={styles.loadingMenu}>{t('common.loading')}</div>
      </Sider>
    );
  }

  return (
    <Sider
      width={256}
      collapsed={collapsed}
      className={`${styles.sider}${isDark ? ` ${styles.siderDark}` : ''}`}
      trigger={null}
    >
      {/* 智能体选择器 */}
      <div className={styles.agentSelectorContainer}>
        <AgentSelector collapsed={collapsed} />
      </div>



      {/* 菜单 */}
      <Menu
        mode="inline"
        selectedKeys={[selectedKey]}
        openKeys={openKeys}
        onOpenChange={handleOpenChange}
        onClick={handleMenuClick}
        items={menuItems}
        className={styles.menu}
      />
    </Sider>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * 根据权限过滤菜单
 */
function filterMenuByPermission(
  menu: MenuItem[],
  hasPermission: (code: string) => boolean
): MenuItem[] {
  return menu
    .filter((item) => {
      // 如果没有设置权限，默认显示
      if (!item.permission) return true;
      // 检查权限
      return hasPermission(item.permission);
    })
    .map((item) => {
      // 递归过滤子菜单
      if (item.children) {
        const filteredChildren = filterMenuByPermission(
          item.children,
          hasPermission
        );
        // 如果子菜单全部被过滤掉，则隐藏父菜单
        if (filteredChildren.length === 0) {
          return null;
        }
        return { ...item, children: filteredChildren };
      }
      return item;
    })
    .filter((item): item is MenuItem => item !== null);
}

/**
 * 将 MenuItem 转换为 Ant Design Menu 格式（支持国际化）
 */
function convertToMenuItems(
  menu: MenuItem[],
  t: (key: string) => string
): any[] {
  return menu.map((item) => {
    const menuItem: any = {
      key: item.key,
      icon: item.icon,
      label: t(item.label),  // 使用 t() 翻译
    };

    if (item.children && item.children.length > 0) {
      menuItem.children = convertToMenuItems(item.children, t);
    }

    return menuItem;
  });
}

/**
 * 查找菜单项的路径
 */
function findMenuPath(menu: MenuItem[], key: string): string | null {
  for (const item of menu) {
    if (item.key === key) {
      return item.path || null;
    }
    if (item.children) {
      const path = findMenuPath(item.children, key);
      if (path) return path;
    }
  }
  return null;
}
