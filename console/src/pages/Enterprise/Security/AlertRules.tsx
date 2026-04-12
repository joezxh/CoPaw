import React, { useState } from "react";
import { Table, Button, Space, Modal, Form, Input, Select, Switch, message, Tabs, InputNumber } from "antd";
import { useRequest } from "ahooks";
import {
  getAlertRules,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  getAlertEvents,
  testNotification,
  AlertRule,
} from "../../../api/modules/enterprise-alerts";

const { Option } = Select;
const { TabPane } = Tabs;

const AlertRules: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [form] = Form.useForm();

  // Rules
  const { data: rulesData, loading: rulesLoading, refresh: refreshRules } = useRequest(getAlertRules);

  // Events
  const { data: eventsData, loading: eventsLoading, refresh: refreshEvents } = useRequest(getAlertEvents, {
    defaultParams: [{ offset: 0, limit: 50 }],
  });

  const handleEdit = (record: AlertRule) => {
    setEditingRule(record);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: "Are you sure you want to delete this rule?",
      onOk: async () => {
        try {
          await deleteAlertRule(id);
          message.success("Rule deleted successfully");
          refreshRules();
        } catch (error: any) {
          message.error(error.message || "Failed to delete rule");
        }
      },
    });
  };

  const handleToggleStatus = async (id: string, is_active: boolean) => {
    try {
      await updateAlertRule(id, { is_active });
      message.success("Rule status updated");
      refreshRules();
    } catch (error: any) {
      message.error(error.message || "Failed to update rule status");
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingRule && editingRule.id) {
        await updateAlertRule(editingRule.id, values);
        message.success("Rule updated successfully");
      } else {
        await createAlertRule(values);
        message.success("Rule created successfully");
      }
      setIsModalVisible(false);
      refreshRules();
    } catch (error: any) {
      if (error?.message) {
        message.error(error.message);
      }
    }
  };

  const handleTestNotification = async () => {
    try {
      await testNotification("This is a manual test alert from the Enterprise Console.");
      message.success("Test notification sent successfully");
      refreshEvents();
    } catch (error: any) {
      message.error(error.message || "Failed to send test notification");
    }
  };

  const ruleColumns = [
    { title: "Rule Type", dataIndex: "rule_type", key: "rule_type" },
    { title: "Description", dataIndex: "description", key: "description" },
    { title: "Threshold", dataIndex: "threshold", key: "threshold", render: (t: number, r: AlertRule) => `${t} per ${r.window_seconds}s` },
    { title: "Channels", dataIndex: "notify_channels", key: "notify_channels", render: (c: string[]) => c?.join(", ") || "None" },
    {
      title: "Status",
      key: "is_active",
      render: (_: any, record: AlertRule) => (
        <Switch checked={record.is_active} onChange={(checked) => handleToggleStatus(record.id, checked)} />
      ),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: any, record: AlertRule) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)}>Edit</Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>Delete</Button>
        </Space>
      ),
    },
  ];

  const eventColumns = [
    { title: "Triggered At", dataIndex: "triggered_at", key: "triggered_at", render: (text: string) => new Date(text).toLocaleString() },
    { title: "Rule Type", dataIndex: "rule_type", key: "rule_type" },
    { title: "Notify Status", dataIndex: "notify_status", key: "notify_status" },
    { title: "Context", dataIndex: "context", key: "context", render: (c: any) => <pre style={{margin:0, fontSize:'12px'}}>{JSON.stringify(c, null, 2)}</pre> },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Security Alerts & Anomalies</h2>
        <Space>
          <Button onClick={handleTestNotification}>Test Notification</Button>
          <Button type="primary" onClick={() => { setEditingRule(null); form.resetFields(); setIsModalVisible(true); }}>
            Create Alert Rule
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="rules">
        <TabPane tab="Alert Rules" key="rules">
          <Table columns={ruleColumns} dataSource={rulesData || []} rowKey="id" loading={rulesLoading} pagination={false} />
        </TabPane>
        <TabPane tab="Alert Events" key="events">
          <Table columns={eventColumns} dataSource={eventsData?.items || []} rowKey="id" loading={eventsLoading} />
        </TabPane>
      </Tabs>

      <Modal title={editingRule ? "Edit Alert Rule" : "Create Alert Rule"} open={isModalVisible} onOk={handleModalOk} onCancel={() => setIsModalVisible(false)}>
        <Form form={form} layout="vertical" initialValues={{ threshold: 3, window_seconds: 300, is_active: true, notify_channels: [] }}>
          <Form.Item name="rule_type" label="Rule Type (e.g., login_fail)" rules={[{ required: true }]}>
            <Input disabled={!!editingRule} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="threshold" label="Threshold Count" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="window_seconds" label="Time Window (seconds)" rules={[{ required: true }]}>
            <InputNumber min={10} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notify_channels" label="Notification Channels">
            <Select mode="tags" placeholder="e.g., wecom, dingtalk, email">
              <Option value="wecom">WeCom</Option>
              <Option value="dingtalk">DingTalk</Option>
              <Option value="email">Email</Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_active" label="Status" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertRules;
