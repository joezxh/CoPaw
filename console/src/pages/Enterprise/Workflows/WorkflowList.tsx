import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Table, Tag, Select, Button, Space, Modal, Form, Input,
  message, Popconfirm, Typography, Tooltip
} from "antd";
import { PlusOutlined, PlayCircleOutlined, DeleteOutlined } from "@ant-design/icons";
import {
  enterpriseWorkflowsApi,
  Workflow, WorkflowCategory, WorkflowStatus
} from "../../../api/modules/enterprise-workflows";

const { Title } = Typography;

const CATEGORY_COLOR: Record<WorkflowCategory, string> = {
  dify: "purple",
  dify_chatflow: "blue",
  dify_agent: "cyan",
  internal: "green",
};

const STATUS_COLOR: Record<WorkflowStatus, string> = {
  draft: "default",
  active: "success",
  archived: "error",
};

export default function WorkflowList() {
  const { t } = useTranslation();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<WorkflowCategory | undefined>();
  const [statusFilter, setStatusFilter] = useState<WorkflowStatus | undefined>();
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res = await enterpriseWorkflowsApi.list({
        category: categoryFilter,
        status: statusFilter,
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setWorkflows(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [categoryFilter, statusFilter, page]);

  const handleCreate = async (values: Record<string, string>) => {
    await enterpriseWorkflowsApi.create(values as any);
    message.success(t("enterprise.workflows.createSuccess"));
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleActivate = async (wf: Workflow) => {
    await enterpriseWorkflowsApi.update(wf.id, {
      status: wf.status === "active" ? "draft" : "active",
    });
    message.success(t("enterprise.workflows.statusUpdated"));
    load();
  };

  const handleExecute = async (wf: Workflow) => {
    const exec = await enterpriseWorkflowsApi.execute(wf.id);
    message.success(t("enterprise.workflows.executionStarted", { id: exec.id }));
  };

  const handleDelete = async (id: string) => {
    await enterpriseWorkflowsApi.delete(id);
    message.success(t("enterprise.workflows.deleteSuccess"));
    load();
  };

  const columns = [
    { title: t("enterprise.workflows.name"), dataIndex: "name", key: "name", ellipsis: true },
    {
      title: t("enterprise.workflows.category"),
      dataIndex: "category",
      key: "category",
      render: (c: WorkflowCategory) => <Tag color={CATEGORY_COLOR[c]}>{t(`enterprise.workflows.category.${c}`)}</Tag>,
    },
    {
      title: t("enterprise.workflows.status"),
      dataIndex: "status",
      key: "status",
      render: (s: WorkflowStatus) => <Tag color={STATUS_COLOR[s]}>{t(`enterprise.workflows.status.${s}`)}</Tag>,
    },
    { title: t("enterprise.workflows.version"), dataIndex: "version", key: "version", width: 80 },
    { title: t("enterprise.workflows.description"), dataIndex: "description", key: "description", ellipsis: true },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: unknown, record: Workflow) => (
        <Space>
          <Button
            size="small"
            type={record.status === "active" ? "default" : "primary"}
            onClick={() => handleActivate(record)}
          >
            {record.status === "active" ? t("enterprise.workflows.deactivate") : t("enterprise.workflows.activate")}
          </Button>
          <Tooltip title={record.status !== "active" ? t("enterprise.workflows.activateFirst") : ""}>
            <Button
              size="small"
              icon={<PlayCircleOutlined />}
              disabled={record.status !== "active"}
              onClick={() => handleExecute(record)}
            >{t("enterprise.workflows.run")}</Button>
          </Tooltip>
          <Popconfirm title={t("enterprise.workflows.deleteConfirm")} onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>{t("common.delete")}</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>{t("enterprise.workflows.title")}</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          {t("enterprise.workflows.addWorkflow")}
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder={t("enterprise.workflows.category")}
          allowClear
          style={{ width: 160 }}
          onChange={(v) => setCategoryFilter(v)}
          options={(["dify", "dify_chatflow", "dify_agent", "internal"] as WorkflowCategory[]).map(
            (c) => ({ label: <Tag color={CATEGORY_COLOR[c]}>{t(`enterprise.workflows.category.${c}`)}</Tag>, value: c })
          )}
        />
        <Select
          placeholder={t("enterprise.workflows.status")}
          allowClear
          style={{ width: 120 }}
          onChange={(v) => setStatusFilter(v)}
          options={(["draft", "active", "archived"] as WorkflowStatus[]).map(
            (s) => ({ label: <Tag color={STATUS_COLOR[s]}>{t(`enterprise.workflows.status.${s}`)}</Tag>, value: s })
          )}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={workflows}
        rowKey="id"
        loading={loading}
        pagination={{ total, pageSize: PAGE_SIZE, current: page, onChange: setPage }}
        size="middle"
      />

      <Modal
        title={t("enterprise.workflows.createWorkflow")}
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label={t("enterprise.workflows.name")} rules={[{ required: true, message: t("enterprise.workflows.nameRequired") }]}><Input /></Form.Item>
          <Form.Item name="category" label={t("enterprise.workflows.category")} initialValue="internal" rules={[{ required: true }]}>
            <Select options={[
              { label: t("enterprise.workflows.category.internal"), value: "internal" },
              { label: t("enterprise.workflows.category.dify"), value: "dify" },
              { label: t("enterprise.workflows.category.dify_chatflow"), value: "dify_chatflow" },
              { label: t("enterprise.workflows.category.dify_agent"), value: "dify_agent" },
            ]} />
          </Form.Item>
          <Form.Item name="description" label={t("enterprise.workflows.description")}><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
