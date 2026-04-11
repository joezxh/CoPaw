import React, { useEffect, useState } from "react";
import {
  Table, Button, Space, Tag, Modal, Form, Input,
  message, Popconfirm, Transfer, Typography, Switch
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, SafetyOutlined } from "@ant-design/icons";
import { enterpriseRolesApi, Role, Permission } from "../../../api/modules/enterprise-roles";

const { Title } = Typography;

const LEVEL_COLORS = ["purple", "blue", "cyan", "green", "orange"];

export default function RoleList() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(false);

  const [createOpen, setCreateOpen] = useState(false);
  const [editRole, setEditRole] = useState<Role | null>(null);
  const [permDrawerRole, setPermDrawerRole] = useState<Role | null>(null);
  const [assignedPermKeys, setAssignedPermKeys] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [permOpen, setPermOpen] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [r, p] = await Promise.all([
        enterpriseRolesApi.listRoles(),
        enterpriseRolesApi.listPermissions(),
      ]);
      setRoles(r);
      setPermissions(p);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (values: Record<string, string>) => {
    await enterpriseRolesApi.createRole(values as any);
    message.success("Role created");
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleUpdate = async (values: Record<string, string>) => {
    if (!editRole) return;
    await enterpriseRolesApi.updateRole(editRole.id, values as any);
    message.success("Role updated");
    setEditRole(null);
    load();
  };

  const handleDelete = async (id: string) => {
    await enterpriseRolesApi.deleteRole(id);
    message.success("Role deleted");
    load();
  };

  const openPermDraw = async (role: Role) => {
    setPermDrawerRole(role);
    const perms = await enterpriseRolesApi.getRolePermissions(role.id);
    setAssignedPermKeys(perms.map((p) => p.id));
    setPermOpen(true);
  };

  const handleSavePerms = async () => {
    if (!permDrawerRole) return;
    await enterpriseRolesApi.setRolePermissions(permDrawerRole.id, assignedPermKeys);
    message.success("Permissions updated");
    setPermOpen(false);
  };

  const columns = [
    { title: "Name", dataIndex: "name", key: "name" },
    {
      title: "Level",
      dataIndex: "level",
      key: "level",
      render: (l: number) => <Tag color={LEVEL_COLORS[l] ?? "default"}>L{l}</Tag>,
    },
    { title: "Description", dataIndex: "description", key: "description" },
    {
      title: "System Role",
      dataIndex: "is_system_role",
      key: "is_system_role",
      render: (v: boolean) => <Switch checked={v} disabled size="small" />,
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: Role) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            disabled={record.is_system_role}
            onClick={() => { setEditRole(record); form.setFieldsValue(record); }}
          >Edit</Button>
          <Button
            size="small"
            icon={<SafetyOutlined />}
            onClick={() => openPermDraw(record)}
          >Permissions</Button>
          <Popconfirm
            title="Delete this role?"
            onConfirm={() => handleDelete(record.id)}
            disabled={record.is_system_role}
          >
            <Button size="small" danger icon={<DeleteOutlined />} disabled={record.is_system_role}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Role Management</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          New Role
        </Button>
      </div>

      <Table columns={columns} dataSource={roles} rowKey="id" loading={loading} size="middle" />

      {/* Create Modal */}
      <Modal
        title="Create Role"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title="Edit Role"
        open={!!editRole}
        onCancel={() => setEditRole(null)}
        onOk={() => form.validateFields().then(handleUpdate)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" initialValues={editRole ?? {}}>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      {/* Permission Assignment Modal */}
      <Modal
        title={`Permissions — ${permDrawerRole?.name}`}
        open={permOpen}
        onCancel={() => setPermOpen(false)}
        onOk={handleSavePerms}
        width={680}
        destroyOnClose
      >
        <Transfer
          dataSource={permissions.map((p) => ({
            key: p.id,
            title: `${p.resource}:${p.action}`,
            description: p.description,
          }))}
          targetKeys={assignedPermKeys}
          onChange={(keys) => setAssignedPermKeys(keys as string[])}
          render={(item) => item.title}
          showSearch
          listStyle={{ width: 280, height: 420 }}
        />
      </Modal>
    </div>
  );
}
