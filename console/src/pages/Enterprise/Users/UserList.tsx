import { useState } from "react";
import {
  Table, Button, Space, Tag, Input, Select,
  Modal, Form, message, Popconfirm, Drawer, Transfer, Typography
} from "antd";
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, KeyOutlined } from "@ant-design/icons";
import { enterpriseUsersApi, User } from "../../../api/modules/enterprise-users";
import { enterpriseRolesApi, Role } from "../../../api/modules/enterprise-roles";
import { useEffect } from "react";

const { Title } = Typography;

const STATUS_COLORS: Record<string, string> = {
  active: "green",
  disabled: "red",
  vacation: "orange",
};

export default function UserList() {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  // Create / Edit modal
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  // Role assignment drawer
  const [roleDrawerOpen, setRoleDrawerOpen] = useState(false);
  const [roleUser, setRoleUser] = useState<User | null>(null);
  const [allRoles, setAllRoles] = useState<Role[]>([]);
  const [assignedRoleKeys, setAssignedRoleKeys] = useState<string[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const res = await enterpriseUsersApi.list({
        search: search || undefined,
        status: statusFilter,
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setUsers(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [search, statusFilter, page]);

  const handleCreate = async (values: Record<string, string>) => {
    await enterpriseUsersApi.create(values as any);
    message.success("User created");
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleUpdate = async (values: Record<string, string>) => {
    if (!editUser) return;
    await enterpriseUsersApi.update(editUser.id, values as any);
    message.success("User updated");
    setEditUser(null);
    load();
  };

  const handleDisable = async (id: string) => {
    await enterpriseUsersApi.disable(id);
    message.success("User disabled");
    load();
  };

  const openRoleDrawer = async (user: User) => {
    setRoleUser(user);
    const [roles, userRoles] = await Promise.all([
      enterpriseRolesApi.listRoles(),
      enterpriseUsersApi.getRoles(user.id),
    ]);
    setAllRoles(roles);
    setAssignedRoleKeys(userRoles.map((r) => r.id));
    setRoleDrawerOpen(true);
  };

  const handleAssignRoles = async () => {
    if (!roleUser) return;
    await enterpriseUsersApi.assignRoles(roleUser.id, assignedRoleKeys);
    message.success("Roles updated");
    setRoleDrawerOpen(false);
  };

  const columns = [
    { title: "Username", dataIndex: "username", key: "username" },
    { title: "Email", dataIndex: "email", key: "email", render: (v?: string) => v ?? "—" },
    { title: "Display Name", dataIndex: "display_name", key: "display_name" },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (s: string) => <Tag color={STATUS_COLORS[s] ?? "default"}>{s}</Tag>,
    },
    {
      title: "MFA",
      dataIndex: "mfa_enabled",
      key: "mfa_enabled",
      render: (v: boolean) => <Tag color={v ? "blue" : "default"}>{v ? "Enabled" : "Disabled"}</Tag>,
    },
    { title: "Last Login", dataIndex: "last_login_at", key: "last_login_at", render: (v?: string) => v ? new Date(v).toLocaleString() : "—" },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: User) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => { setEditUser(record); form.setFieldsValue(record); }}>Edit</Button>
          <Button size="small" icon={<KeyOutlined />} onClick={() => openRoleDrawer(record)}>Roles</Button>
          <Popconfirm title="Disable this user?" onConfirm={() => handleDisable(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} disabled={record.status === "disabled"}>Disable</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>User Management</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          New User
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder="Search username or email"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 260 }}
          allowClear
        />
        <Select
          placeholder="Status"
          allowClear
          style={{ width: 140 }}
          onChange={setStatusFilter}
          options={[
            { label: "Active", value: "active" },
            { label: "Disabled", value: "disabled" },
            { label: "Vacation", value: "vacation" },
          ]}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{ total, pageSize: PAGE_SIZE, current: page, onChange: setPage }}
        size="middle"
      />

      {/* Create Modal */}
      <Modal
        title="Create User"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, min: 8 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="email" label="Email"><Input /></Form.Item>
          <Form.Item name="display_name" label="Display Name"><Input /></Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title="Edit User"
        open={!!editUser}
        onCancel={() => setEditUser(null)}
        onOk={() => form.validateFields().then(handleUpdate)}
        destroyOnClose
      >
        <Form form={form} layout="vertical" initialValues={editUser ?? {}}>
          <Form.Item name="email" label="Email"><Input /></Form.Item>
          <Form.Item name="display_name" label="Display Name"><Input /></Form.Item>
          <Form.Item name="status" label="Status">
            <Select options={[
              { label: "Active", value: "active" },
              { label: "Disabled", value: "disabled" },
              { label: "Vacation", value: "vacation" },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Role Drawer */}
      <Drawer
        title={`Assign Roles — ${roleUser?.username}`}
        open={roleDrawerOpen}
        onClose={() => setRoleDrawerOpen(false)}
        extra={<Button type="primary" onClick={handleAssignRoles}>Save</Button>}
        width={560}
      >
        <Transfer
          dataSource={allRoles.map((r) => ({ key: r.id, title: `${r.name} (L${r.level})`, description: r.description }))}
          targetKeys={assignedRoleKeys}
          onChange={(keys) => setAssignedRoleKeys(keys as string[])}
          render={(item) => item.title}
          showSearch
          listStyle={{ width: 240, height: 400 }}
        />
      </Drawer>
    </div>
  );
}
