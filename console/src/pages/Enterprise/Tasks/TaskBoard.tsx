import { useEffect, useState } from "react";
import {
  Table, Tag, Select, Input, Space, Button,
  Modal, Form, DatePicker, message, Typography, Badge
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { enterpriseTasksApi, Task, TaskStatus, TaskPriority } from "../../../api/modules/enterprise-tasks";
import dayjs from "dayjs";

const { Title } = Typography;

const STATUS_COLOR: Record<TaskStatus, string> = {
  pending: "default",
  in_progress: "processing",
  blocked: "warning",
  completed: "success",
  cancelled: "error",
};

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  high: "red",
  medium: "orange",
  low: "blue",
};

const STATUS_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  pending: ["in_progress", "cancelled"],
  in_progress: ["completed", "blocked", "cancelled"],
  blocked: ["in_progress", "cancelled"],
  completed: [],
  cancelled: [],
};

export default function TaskBoard() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | undefined>();
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | undefined>();
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();

  const load = async () => {
    setLoading(true);
    try {
      const res = await enterpriseTasksApi.list({
        status: statusFilter,
        priority: priorityFilter,
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setTasks(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [statusFilter, priorityFilter, page]);

  const handleCreate = async (values: Record<string, unknown>) => {
    const data = {
      ...values,
      due_date: values.due_date ? dayjs(values.due_date as string).toISOString() : undefined,
    };
    await enterpriseTasksApi.create(data as any);
    message.success("Task created");
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleStatusChange = async (task: Task, newStatus: TaskStatus) => {
    await enterpriseTasksApi.changeStatus(task.id, newStatus);
    message.success(`Status → ${newStatus}`);
    load();
  };

  const columns = [
    { title: "Title", dataIndex: "title", key: "title", ellipsis: true },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 140,
      render: (s: TaskStatus, record: Task) => (
        <Select
          size="small"
          value={s}
          style={{ width: 130 }}
          onChange={(v) => handleStatusChange(record, v)}
          options={STATUS_TRANSITIONS[s].map((st) => ({ label: st, value: st }))}
          dropdownMatchSelectWidth={false}
        >
          <Badge status={STATUS_COLOR[s] as any} text={s} />
        </Select>
      ),
    },
    {
      title: "Priority",
      dataIndex: "priority",
      key: "priority",
      render: (p: TaskPriority) => <Tag color={PRIORITY_COLOR[p]}>{p}</Tag>,
    },
    {
      title: "Due",
      dataIndex: "due_date",
      key: "due_date",
      render: (v?: string) => v ? dayjs(v).format("MMM D, YYYY") : "—",
    },
    { title: "Created", dataIndex: "created_at", key: "created_at", render: (v: string) => dayjs(v).format("MM/DD HH:mm") },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Task Board</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          New Task
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Status"
          allowClear
          style={{ width: 140 }}
          onChange={(v) => setStatusFilter(v)}
          options={(["pending", "in_progress", "blocked", "completed", "cancelled"] as TaskStatus[]).map((s) => ({
            label: <Badge status={STATUS_COLOR[s] as any} text={s} />,
            value: s,
          }))}
        />
        <Select
          placeholder="Priority"
          allowClear
          style={{ width: 120 }}
          onChange={(v) => setPriorityFilter(v)}
          options={(["high", "medium", "low"] as TaskPriority[]).map((p) => ({
            label: <Tag color={PRIORITY_COLOR[p]}>{p}</Tag>,
            value: p,
          }))}
        />
      </Space>

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading}
        pagination={{ total, pageSize: PAGE_SIZE, current: page, onChange: setPage }}
        size="middle"
      />

      <Modal
        title="Create Task"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label="Title" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="description" label="Description"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="priority" label="Priority" initialValue="medium">
            <Select options={[
              { label: "High", value: "high" },
              { label: "Medium", value: "medium" },
              { label: "Low", value: "low" },
            ]} />
          </Form.Item>
          <Form.Item name="due_date" label="Due Date">
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
