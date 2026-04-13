import { useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
    message.success(t("enterprise.users.createSuccess"));
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleUpdate = async (values: Record<string, string>) => {
    if (!editUser) return;
    await enterpriseUsersApi.update(editUser.id, values as any);
    message.success(t("enterprise.users.updateSuccess"));
    setEditUser(null);
    load();
  };

  const handleDisable = async (id: string) => {
    await enterpriseUsersApi.disable(id);
    message.success(t("enterprise.users.disableSuccess"));
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
    message.success(t("enterprise.users.rolesUpdated"));
    setRoleDrawerOpen(false);
  };

  const columns = [
    { title: t("enterprise.users.username"), dataIndex: "username", key: "username" },
    { title: t("enterprise.users.email"), dataIndex: "email", key: "email", render: (v?: string) => v ?? "—" },
    { title: t("enterprise.users.displayName"), dataIndex: "display_name", key: "display_name" },
    {
      title: t("enterprise.users.status"),
      dataIndex: "status",
      key: "status",
      render: (s: string) => <Tag color={STATUS_COLORS[s] ?? "default"}>{t(`enterprise.users.status.${s}`)}</Tag>,
    },
    {
      title: t("enterprise.users.mfa"),
      dataIndex: "mfa_enabled",
      key: "mfa_enabled",
      render: (v: boolean) => <Tag color={v ? "blue" : "default"}>{v ? t("common.enabled") : t("common.disabled")}</Tag>,
    },
    { title: t("enterprise.users.lastLogin"), dataIndex: "last_login_at", key: "last_login_at", render: (v?: string) => v ? new Date(v).toLocaleString() : "—" },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: unknown, record: User) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => { setEditUser(record); form.setFieldsValue(record); }}>{t("common.edit")}</Button>
          <Button size="small" icon={<KeyOutlined />} onClick={() => openRoleDrawer(record)}>{t("enterprise.users.roles")}</Button>
          <Popconfirm title={t("enterprise.users.disableConfirm")} onConfirm={() => handleDisable(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} disabled={record.status === "disabled"}>{t("enterprise.users.disable")}</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>{t("enterprise.users.title")}</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          {t("enterprise.users.addUser")}
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Input
          prefix={<SearchOutlined />}
          placeholder={t("enterprise.users.searchPlaceholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 260 }}
          allowClear
        />
        <Select
          placeholder={t("enterprise.users.status")}
          allowClear
          style={{ width: 140 }}
          onChange={setStatusFilter}
          options={[
            { label: t("enterprise.users.status.active"), value: "active" },
            { label: t("enterprise.users.status.disabled"), value: "disabled" },
            { label: t("enterprise.users.status.vacation"), value: "vacation" },
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
        title={t("enterprise.users.createUser")}
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="username" label={t("enterprise.users.username")} rules={[{ required: true, message: t("enterprise.users.usernameRequired") }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label={t("enterprise.users.password")} rules={[{ required: true, min: 8, message: t("enterprise.users.passwordMinLength") }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="email" label={t("enterprise.users.email")}><Input /></Form.Item>
          <Form.Item name="display_name" label={t("enterprise.users.displayName")}><Input /></Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title={t("enterprise.users.editUser")}
        open={!!editUser}
        onCancel={() => setEditUser(null)}
        onOk={() => form.validateFields().then(handleUpdate)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form form={form} layout="vertical" initialValues={editUser ?? {}}>
          <Form.Item name="email" label={t("enterprise.users.email")}><Input /></Form.Item>
          <Form.Item name="display_name" label={t("enterprise.users.displayName")}><Input /></Form.Item>
          <Form.Item name="status" label={t("enterprise.users.status")}>
            <Select options={[
              { label: t("enterprise.users.status.active"), value: "active" },
              { label: t("enterprise.users.status.disabled"), value: "disabled" },
              { label: t("enterprise.users.status.vacation"), value: "vacation" },
            ]} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Role Drawer */}
      <Drawer
        title={`${t("enterprise.users.assignRoles")} — ${roleUser?.username}`}
        open={roleDrawerOpen}
        onClose={() => setRoleDrawerOpen(false)}
        extra={<Button type="primary" onClick={handleAssignRoles}>{t("common.save")}</Button>}
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
