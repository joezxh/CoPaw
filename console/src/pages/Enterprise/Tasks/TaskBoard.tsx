import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
    message.success(t("enterprise.tasks.createSuccess"));
    setCreateOpen(false);
    form.resetFields();
    load();
  };

  const handleStatusChange = async (task: Task, newStatus: TaskStatus) => {
    await enterpriseTasksApi.changeStatus(task.id, newStatus);
    message.success(t("enterprise.tasks.statusUpdated", { status: t(`enterprise.tasks.status.${newStatus}`) }));
    load();
  };

  const columns = [
    { title: t("enterprise.tasks.title"), dataIndex: "title", key: "title", ellipsis: true },
    {
      title: t("enterprise.tasks.status"),
      dataIndex: "status",
      key: "status",
      width: 140,
      render: (s: TaskStatus, record: Task) => (
        <Select
          size="small"
          value={s}
          style={{ width: 130 }}
          onChange={(v) => handleStatusChange(record, v)}
          options={STATUS_TRANSITIONS[s].map((st) => ({ label: t(`enterprise.tasks.status.${st}`), value: st }))}
          dropdownMatchSelectWidth={false}
        >
          <Badge status={STATUS_COLOR[s] as any} text={t(`enterprise.tasks.status.${s}`)} />
        </Select>
      ),
    },
    {
      title: t("enterprise.tasks.priority"),
      dataIndex: "priority",
      key: "priority",
      render: (p: TaskPriority) => <Tag color={PRIORITY_COLOR[p]}>{t(`enterprise.tasks.priority.${p}`)}</Tag>,
    },
    {
      title: t("enterprise.tasks.dueDate"),
      dataIndex: "due_date",
      key: "due_date",
      render: (v?: string) => v ? dayjs(v).format("MMM D, YYYY") : "—",
    },
    { title: t("enterprise.tasks.createdAt"), dataIndex: "created_at", key: "created_at", render: (v: string) => dayjs(v).format("MM/DD HH:mm") },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>{t("enterprise.tasks.title_page")}</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          {t("enterprise.tasks.addTask")}
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder={t("enterprise.tasks.status")}
          allowClear
          style={{ width: 140 }}
          onChange={(v) => setStatusFilter(v)}
          options={(["pending", "in_progress", "blocked", "completed", "cancelled"] as TaskStatus[]).map((s) => ({
            label: <Badge status={STATUS_COLOR[s] as any} text={t(`enterprise.tasks.status.${s}`)} />,
            value: s,
          }))}
        />
        <Select
          placeholder={t("enterprise.tasks.priority")}
          allowClear
          style={{ width: 120 }}
          onChange={(v) => setPriorityFilter(v)}
          options={(["high", "medium", "low"] as TaskPriority[]).map((p) => ({
            label: <Tag color={PRIORITY_COLOR[p]}>{t(`enterprise.tasks.priority.${p}`)}</Tag>,
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
        title={t("enterprise.tasks.createTask")}
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); }}
        onOk={() => form.validateFields().then(handleCreate)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Form.Item name="title" label={t("enterprise.tasks.title")} rules={[{ required: true, message: t("enterprise.tasks.titleRequired") }]}><Input /></Form.Item>
          <Form.Item name="description" label={t("enterprise.tasks.description")}><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="priority" label={t("enterprise.tasks.priority")} initialValue="medium">
            <Select options={[
              { label: t("enterprise.tasks.priority.high"), value: "high" },
              { label: t("enterprise.tasks.priority.medium"), value: "medium" },
              { label: t("enterprise.tasks.priority.low"), value: "low" },
            ]} />
          </Form.Item>
          <Form.Item name="due_date" label={t("enterprise.tasks.dueDate")}>
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
