import React, { useState } from "react";
import { Table, Button, Space, Modal, Form, Input, Select, Switch, message, Tag, Tabs } from "antd";
import { useRequest } from "ahooks";
import {
  getRules,
  getBuiltinRules,
  createRule,
  updateRule,
  deleteRule,
  getEvents,
  DLPRule,
  DLPEvent,
} from "../../../api/modules/enterprise-dlp";

const { Option } = Select;
const { TabPane } = Tabs;

const DLPRules: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingRule, setEditingRule] = useState<DLPRule | null>(null);
  const [form] = Form.useForm();

  // Custom Rules
  const { data: rulesData, loading: rulesLoading, refresh: refreshRules } = useRequest(getRules, {
    defaultParams: [{ offset: 0, limit: 50 }],
  });

  // Builtin Rules
  const { data: builtinRules, loading: builtinLoading } = useRequest(getBuiltinRules);

  // Events
  const { data: eventsData, loading: eventsLoading } = useRequest(getEvents, {
    defaultParams: [{ offset: 0, limit: 50 }],
  });

  const handleEdit = (record: DLPRule) => {
    setEditingRule(record);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: "Are you sure you want to delete this rule?",
      onOk: async () => {
        try {
          await deleteRule(id);
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
      await updateRule(id, { is_active });
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
        await updateRule(editingRule.id, values);
        message.success("Rule updated successfully");
      } else {
        await createRule(values);
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

  const renderActionTag = (action: string) => {
    const colorMap: Record<string, string> = {
      mask: "blue",
      alert: "warning",
      block: "error",
    };
    return <Tag color={colorMap[action] || "default"}>{action.toUpperCase()}</Tag>;
  };

  const customRuleColumns = [
    { title: "Rule Name", dataIndex: "rule_name", key: "rule_name" },
    { title: "Description", dataIndex: "description", key: "description" },
    { title: "Action", dataIndex: "action", key: "action", render: renderActionTag },
    {
      title: "Status",
      key: "is_active",
      render: (_: any, record: DLPRule) => (
        <Switch
          checked={record.is_active}
          onChange={(checked) => handleToggleStatus(record.id as string, checked)}
        />
      ),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: any, record: DLPRule) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)}>Edit</Button>
          <Button type="link" danger onClick={() => handleDelete(record.id as string)}>Delete</Button>
        </Space>
      ),
    },
  ];

  const builtinRuleColumns = [
    { title: "Built-in Rule Name", dataIndex: "rule_name", key: "rule_name" },
    { title: "Description", dataIndex: "description", key: "description" },
    { title: "Action", dataIndex: "action", key: "action", render: renderActionTag },
    { title: "Pattern", dataIndex: "pattern_regex", key: "pattern_regex", render: (p: string) => <code>{p}</code> },
  ];

  const eventColumns = [
    { title: "Triggered At", dataIndex: "triggered_at", key: "triggered_at", render: (text: string) => new Date(text).toLocaleString() },
    { title: "Rule", dataIndex: "rule_name", key: "rule_name" },
    { title: "Action Taken", dataIndex: "action_taken", key: "action_taken", render: renderActionTag },
    { title: "Context Path", dataIndex: "context_path", key: "context_path" },
    { title: "Summary", dataIndex: "content_summary", key: "content_summary" },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Data Loss Prevention (DLP)</h2>
        <Button
          type="primary"
          onClick={() => {
            setEditingRule(null);
            form.resetFields();
            setIsModalVisible(true);
          }}
        >
          Create Custom Rule
        </Button>
      </div>

      <Tabs defaultActiveKey="custom">
        <TabPane tab="Custom Rules" key="custom">
          <Table columns={customRuleColumns} dataSource={rulesData?.items || []} rowKey="id" loading={rulesLoading} />
        </TabPane>
        <TabPane tab="Built-in Rules" key="builtin">
          <Table columns={builtinRuleColumns} dataSource={builtinRules || []} rowKey="rule_name" loading={builtinLoading} pagination={false} />
        </TabPane>
        <TabPane tab="Violation Events" key="events">
          <Table columns={eventColumns} dataSource={eventsData?.items || []} rowKey="id" loading={eventsLoading} />
        </TabPane>
      </Tabs>

      <Modal title={editingRule ? "Edit Rule" : "Create Rule"} open={isModalVisible} onOk={handleModalOk} onCancel={() => setIsModalVisible(false)}>
        <Form form={form} layout="vertical" initialValues={{ action: "alert", is_active: true }}>
          <Form.Item name="rule_name" label="Rule Name" rules={[{ required: true }]}>
            <Input disabled={!!editingRule} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="pattern_regex" label="Regex Pattern" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="action" label="Action" rules={[{ required: true }]}>
            <Select>
              <Option value="mask">Mask (Redact)</Option>
              <Option value="alert">Alert Log Only</Option>
              <Option value="block">Block Request</Option>
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

export default DLPRules;
