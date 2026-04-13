/**
 * 权限控制 Hook
 *
 * 功能：
 * 1. 从 API 获取用户权限
 * 2. 提供 hasPermission() 检查方法
 * 3. 缓存权限数据
 * 4. 支持权限树构建
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { getApiUrl, getApiToken } from '../api/config';

// ============================================================================
// Types
// ============================================================================

export interface Permission {
  id: string;
  tenant_id: string;
  permission_code: string;
  resource: string;
  action: string;
  resource_path?: string;
  permission_type: 'menu' | 'api' | 'button' | 'data';
  description?: string;
  parent_id?: string;
  sort_order: number;
  icon?: string;
  is_visible: boolean;
  created_by?: string;
}

export interface UserPermissionsResponse {
  user_id: string;
  permissions: Permission[];
  roles: string[];
}

// ============================================================================
// Hook
// ============================================================================

interface UsePermissionsReturn {
  permissions: Permission[];
  roles: string[];
  loading: boolean;
  error: Error | null;
  hasPermission: (permissionCode: string) => boolean;
  hasAnyPermission: (permissionCodes: string[]) => boolean;
  hasAllPermissions: (permissionCodes: string[]) => boolean;
  getPermissionsByType: (type: Permission['permission_type']) => Permission[];
  getMenuPermissions: () => Permission[];
  refreshPermissions: () => Promise<void>;
}

/**
 * 权限控制 Hook
 * 
 * 用法：
 * ```tsx
 * const { hasPermission, loading } = usePermissions();
 * 
 * if (hasPermission('agent:config:read')) {
 *   // 显示 Agent 配置菜单
 * }
 * ```
 */
export function usePermissions(): UsePermissionsReturn {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [roles, setRoles] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // 加载用户权限
  const loadPermissions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = getApiToken();
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // 如果有 token，添加到请求头
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(getApiUrl('/v1/auth/permissions'), {
        method: 'GET',
        headers,
        credentials: 'include',
      });

      if (!response.ok) {
        // 401 表示未授权，可能是 token 无效或过期
        if (response.status === 401) {
          console.warn('[usePermissions] 401 Unauthorized - 用户未登录或 token 无效');
          setPermissions([]);
          setRoles([]);
          setLoading(false);
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: UserPermissionsResponse = await response.json();
      setPermissions(data.permissions);
      setRoles(data.roles);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to load permissions');
      setError(error);
      console.error('[usePermissions] Failed to load permissions:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    loadPermissions();
  }, [loadPermissions]);

  // 权限检查：单个权限
  const hasPermission = useCallback(
    (permissionCode: string): boolean => {
      // 系统管理员拥有所有权限
      if (roles.includes('系统管理员')) {
        return true;
      }

      return permissions.some((p) => p.permission_code === permissionCode);
    },
    [permissions, roles]
  );

  // 权限检查：任意一个权限
  const hasAnyPermission = useCallback(
    (permissionCodes: string[]): boolean => {
      if (roles.includes('系统管理员')) {
        return true;
      }

      return permissionCodes.some((code) => hasPermission(code));
    },
    [hasPermission, roles]
  );

  // 权限检查：所有权限
  const hasAllPermissions = useCallback(
    (permissionCodes: string[]): boolean => {
      if (roles.includes('系统管理员')) {
        return true;
      }

      return permissionCodes.every((code) => hasPermission(code));
    },
    [hasPermission, roles]
  );

  // 按类型获取权限
  const getPermissionsByType = useCallback(
    (type: Permission['permission_type']): Permission[] => {
      return permissions.filter((p) => p.permission_type === type);
    },
    [permissions]
  );

  // 获取菜单权限
  const getMenuPermissions = useCallback((): Permission[] => {
      return permissions.filter(
        (p) => p.permission_type === 'menu' && p.is_visible
      );
    },
    [permissions]
  );

  // 记忆化返回值
  const value = useMemo<UsePermissionsReturn>(
    () => ({
      permissions,
      roles,
      loading,
      error,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      getPermissionsByType,
      getMenuPermissions,
      refreshPermissions: loadPermissions,
    }),
    [
      permissions,
      roles,
      loading,
      error,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      getPermissionsByType,
      getMenuPermissions,
      loadPermissions,
    ]
  );

  return value;
}

// ============================================================================
// 权限树构建工具函数
// ============================================================================

export interface PermissionTreeNode extends Permission {
  children: PermissionTreeNode[];
}

/**
 * 将权限列表转换为树结构
 */
export function buildPermissionTree(
  permissions: Permission[],
  type: Permission['permission_type'] = 'menu'
): PermissionTreeNode[] {
  // 过滤指定类型的权限
  const filteredPerms = permissions.filter(
    (p) => p.permission_type === type
  );

  // 创建映射
  const permMap = new Map<string, PermissionTreeNode>();
  const rootNodes: PermissionTreeNode[] = [];

  // 初始化节点
  filteredPerms.forEach((perm) => {
    permMap.set(perm.id, { ...perm, children: [] });
  });

  // 构建树
  filteredPerms.forEach((perm) => {
    const node = permMap.get(perm.id)!;

    if (perm.parent_id && permMap.has(perm.parent_id)) {
      // 有父节点，添加到父节点的 children
      const parentNode = permMap.get(perm.parent_id)!;
      parentNode.children.push(node);
    } else {
      // 根节点
      rootNodes.push(node);
    }
  });

  // 按 sort_order 排序
  const sortTree = (nodes: PermissionTreeNode[]): PermissionTreeNode[] => {
    return nodes
      .sort((a, b) => a.sort_order - b.sort_order)
      .map((node) => ({
        ...node,
        children: sortTree(node.children),
      }));
  };

  return sortTree(rootNodes);
}
