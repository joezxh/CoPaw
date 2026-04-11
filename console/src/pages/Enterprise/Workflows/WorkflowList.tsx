import React, { useEffect, useState } from "react";
import {
  Table, Tag, Select, Button, Space, Modal, Form, Input,
  message, Popconfirm, Typography, Tooltip
} from "antd";
import { PlusOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
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
    message.success("Workflow created");
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleActivate = async (wf: Workflow) => {
    await enterpriseWorkflowsApi.update(wf.id, {
      status: wf.status === "active" ? "draft" : "active",
    });
    message.success("Status updated");
    load();
  };

  const handleExecute = async (wf: Workflow) => {
    const exec = await enterpriseWorkflowsApi.execute(wf.id);
    message.success(`Execution started: ${exec.id}`);
  };

  const handleDelete = async (id: string) => {
    await enterpriseWorkflowsApi.delete(id);
    message.success("Workflow deleted");
    load();
  };

  const columns = [
    { title: "Name", dataIndex: "name", key: "name", ellipsis: true },
    {
      title: "Category",
      dataIndex: "category",
      key: "category",
      render: (c: WorkflowCategory) => <Tag color={CATEGORY_COLOR[c]}>{c}</Tag>,
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (s: WorkflowStatus) => <Tag color={STATUS_COLOR[s]}>{s}</Tag>,
    },
    { title: "Version", dataIndex: "version", key: "version", width: 80 },
    { title: "Description", dataIndex: "description", key: "description", ellipsis: true },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: Workflow) => (
        <Space>
          <Button
            size="small"
            type={record.status === "active" ? "default" : "primary"}
            onClick={() => handleActivate(record)}
          >
            {record.status === "active" ? "Deactivate" : "Activate"}
          </Button>
          <Tooltip title={record.status !== "active" ? "Activate first" : ""}>
            <Button
              size="small"
              icon={<PlayCircleOutlined />}
              disabled={record.status !== "active"}
              onClick={() => handleExecute(record)}
            >Run</Button>
          </Tooltip>
          <Popconfirm title="Delete workflow?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />}>Delete</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Workflow Management</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          New Workflow
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Category"
          allowClear
          style={{ width: 160 }}
          onChange={(v) => setCategoryFilter(v)}
          options={(["dify", "dify_chatflow", "dify_agent", "internal"] as WorkflowCategory[]).map(
            (c) => ({ label: <Tag color={CATEGORY_COLOR[c]}>{c}</Tag>, value: c })
          )}
        />
        <Select
          placeholder="Status"
          allowClear
          style={{ width: 120 }}
          onChange={(v) => setStatusFilter(v)}
          options={(["draft", "active", "archived"] as WorkflowStatus[]).map(
            (s) => ({ label: <Tag color={STATUS_COLOR[s]}>{s}</Tag>, value: s })
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
        title="Create Workflow"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Name" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="category" label="Category" initialValue="internal" rules={[{ required: true }]}>
            <Select options={[
              { label: "Internal", value: "internal" },
              { label: "Dify", value: "dify" },
              { label: "Dify Chatflow", value: "dify_chatflow" },
              { label: "Dify Agent", value: "dify_agent" },
            ]} />
          </Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
