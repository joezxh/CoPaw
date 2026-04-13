/**
 * 权限守卫组件
 *
 * 类似 Vue 的 v-permission 指令，根据权限显示/隐藏组件
 *
 * 用法：
 * ```tsx
 * // 单个权限
 * <PermissionGuard permission="agent:config:read">
 *   <AgentConfig />
 * </PermissionGuard>
 *
 * // 多个权限（任意一个）
 * <PermissionGuard permissions={['agent:config:read', 'agent:config:write']}>
 *   <AgentManagement />
 * </PermissionGuard>
 *
 * // 自定义 fallback
 * <PermissionGuard permission="admin:only" fallback={<NoAccess />}>
 *   <AdminPanel />
 * </PermissionGuard>
 * ```
 */
import React from 'react';
import { usePermissions } from '../hooks/usePermissions';

// ============================================================================
// Types
// ============================================================================

export interface PermissionGuardProps {
  /** 单个权限码 */
  permission?: string;
  /** 多个权限码（满足任意一个即可） */
  permissions?: string[];
  /** 无权限时的 fallback 内容 */
  fallback?: React.ReactNode;
  /** 子组件 */
  children: React.ReactNode;
  /** 加载中的 fallback */
  loadingFallback?: React.ReactNode;
}

// ============================================================================
// Component
// ============================================================================

/**
 * 权限守卫组件
 * 
 * 根据用户权限决定是否渲染子组件
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  permissions,
  fallback = null,
  children,
  loadingFallback = null,
}) => {
  const { hasPermission, hasAnyPermission, loading } = usePermissions();

  // 加载中
  if (loading) {
    return <>{loadingFallback}</>;
  }

  // 检查权限
  let hasAccess = false;

  if (permission) {
    // 单个权限检查
    hasAccess = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    // 多个权限检查（任意一个）
    hasAccess = hasAnyPermission(permissions);
  } else {
    // 没有指定权限，默认允许
    hasAccess = true;
  }

  // 有权限，渲染子组件
  if (hasAccess) {
    return <>{children}</>;
  }

  // 无权限，渲染 fallback
  return <>{fallback}</>;
};

// ============================================================================
// 便捷组件：按钮权限守卫
// ============================================================================

export interface PermissionButtonProps
  extends Omit<PermissionGuardProps, 'fallback' | 'children'> {
  /** 按钮组件 */
  button: React.ReactElement;
  /** 禁用时是否显示（true=显示但禁用，false=完全隐藏） */
  showWhenDisabled?: boolean;
}

/**
 * 按钮权限守卫
 * 
 * 无权限时可以禁用按钮或隐藏按钮
 */
export const PermissionButton: React.FC<PermissionButtonProps> = ({
  permission,
  permissions,
  button,
  showWhenDisabled = false,
}) => {
  const { hasPermission, hasAnyPermission, loading } = usePermissions();

  if (loading) {
    return null;
  }

  // 检查权限
  let hasAccess = false;

  if (permission) {
    hasAccess = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    hasAccess = hasAnyPermission(permissions);
  } else {
    hasAccess = true;
  }

  // 有权限，渲染按钮
  if (hasAccess) {
    return button;
  }

  // 无权限
  if (showWhenDisabled) {
    // 显示但禁用
    return React.cloneElement(button, { disabled: true });
  }

  // 完全隐藏
  return null;
};

// ============================================================================
// HOC：高阶组件包装器
// ============================================================================

/**
 * 权限保护高阶组件
 * 
 * 用法：
 * ```tsx
 * const ProtectedComponent = withPermission(MyComponent, 'admin:access');
 * ```
 */
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  permission: string
): React.FC<P> {
  const WrappedComponent: React.FC<P> = (props) => {
    return (
      <PermissionGuard permission={permission}>
        <Component {...props} />
      </PermissionGuard>
    );
  };

  WrappedComponent.displayName = `withPermission(${Component.displayName || Component.name})`;

  return WrappedComponent;
}
