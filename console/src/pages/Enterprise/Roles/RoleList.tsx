import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Table, Button, Space, Tag, Modal, Form, Input,
  message, Popconfirm, Transfer, Typography, Switch
} from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined, SafetyOutlined } from "@ant-design/icons";
import { enterpriseRolesApi, Role, Permission } from "../../../api/modules/enterprise-roles";

const { Title } = Typography;

const LEVEL_COLORS = ["purple", "blue", "cyan", "green", "orange"];

export default function RoleList() {
  const { t } = useTranslation();
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
    message.success(t("enterprise.roles.createSuccess"));
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleUpdate = async (values: Record<string, string>) => {
    if (!editRole) return;
    await enterpriseRolesApi.updateRole(editRole.id, values as any);
    message.success(t("enterprise.roles.updateSuccess"));
    setEditRole(null);
    load();
  };

  const handleDelete = async (id: string) => {
    await enterpriseRolesApi.deleteRole(id);
    message.success(t("enterprise.roles.deleteSuccess"));
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
    message.success(t("enterprise.roles.permissionsUpdated"));
    setPermOpen(false);
  };

  const columns = [
    { title: t("enterprise.roles.name"), dataIndex: "name", key: "name" },
    {
      title: t("enterprise.roles.level"),
      dataIndex: "level",
      key: "level",
      render: (l: number) => <Tag color={LEVEL_COLORS[l] ?? "default"}>L{l}</Tag>,
    },
    { title: t("enterprise.roles.description"), dataIndex: "description", key: "description" },
    {
      title: t("enterprise.roles.systemRole"),
      dataIndex: "is_system_role",
      key: "is_system_role",
      render: (v: boolean) => <Switch checked={v} disabled size="small" />,
    },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: unknown, record: Role) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            disabled={record.is_system_role}
            onClick={() => { setEditRole(record); form.setFieldsValue(record); }}
          >{t("common.edit")}</Button>
          <Button
            size="small"
            icon={<SafetyOutlined />}
            onClick={() => openPermDraw(record)}
          >{t("enterprise.roles.permissions")}</Button>
          <Popconfirm
            title={t("enterprise.roles.deleteConfirm")}
            onConfirm={() => handleDelete(record.id)}
            disabled={record.is_system_role}
          >
            <Button size="small" danger icon={<DeleteOutlined />} disabled={record.is_system_role}>
              {t("common.delete")}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>{t("enterprise.roles.title")}</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          {t("enterprise.roles.addRole")}
        </Button>
      </div>

      <Table columns={columns} dataSource={roles} rowKey="id" loading={loading} size="middle" />

      {/* Create Modal */}
      <Modal
        title={t("enterprise.roles.createRole")}
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t("enterprise.roles.name")} rules={[{ required: true, message: t("enterprise.roles.nameRequired") }]}><Input /></Form.Item>
          <Form.Item name="description" label={t("enterprise.roles.description")}><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title={t("enterprise.roles.editRole")}
        open={!!editRole}
        onCancel={() => setEditRole(null)}
        onOk={() => form.validateFields().then(handleUpdate)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form form={form} layout="vertical" initialValues={editRole ?? {}}>
          <Form.Item name="description" label={t("enterprise.roles.description")}><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      {/* Permission Assignment Modal */}
      <Modal
        title={`${t("enterprise.roles.permissions")} — ${permDrawerRole?.name}`}
        open={permOpen}
        onCancel={() => setPermOpen(false)}
        onOk={handleSavePerms}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
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
