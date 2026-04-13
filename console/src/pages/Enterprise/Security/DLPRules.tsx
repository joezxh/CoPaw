import React, { useState } from "react";
import { useTranslation } from "react-i18next";
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
} from "../../../api/modules/enterprise-dlp";

const { Option } = Select;
const { TabPane } = Tabs;

const DLPRules: React.FC = () => {
  const { t } = useTranslation();
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
      title: t("enterprise.dlp.deleteConfirm"),
      onOk: async () => {
        try {
          await deleteRule(id);
          message.success(t("enterprise.dlp.deleteSuccess"));
          refreshRules();
        } catch (error: any) {
          message.error(error.message || t("enterprise.dlp.deleteFailed"));
        }
      },
    });
  };

  const handleToggleStatus = async (id: string, is_active: boolean) => {
    try {
      await updateRule(id, { is_active });
      message.success(t("enterprise.dlp.statusUpdated"));
      refreshRules();
    } catch (error: any) {
      message.error(error.message || t("enterprise.dlp.updateFailed"));
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingRule && editingRule.id) {
        await updateRule(editingRule.id, values);
        message.success(t("enterprise.dlp.updateSuccess"));
      } else {
        await createRule(values);
        message.success(t("enterprise.dlp.createSuccess"));
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
    return <Tag color={colorMap[action] || "default"}>{t(`enterprise.dlp.action.${action}`)}</Tag>;
  };

  const customRuleColumns = [
    { title: t("enterprise.dlp.ruleName"), dataIndex: "rule_name", key: "rule_name" },
    { title: t("enterprise.dlp.description"), dataIndex: "description", key: "description" },
    { title: t("enterprise.dlp.action"), dataIndex: "action", key: "action", render: renderActionTag },
    {
      title: t("enterprise.dlp.status"),
      key: "is_active",
      render: (_: any, record: DLPRule) => (
        <Switch
          checked={record.is_active}
          onChange={(checked) => handleToggleStatus(record.id as string, checked)}
        />
      ),
    },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: any, record: DLPRule) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)}>{t("common.edit")}</Button>
          <Button type="link" danger onClick={() => handleDelete(record.id as string)}>{t("common.delete")}</Button>
        </Space>
      ),
    },
  ];

  const builtinRuleColumns = [
    { title: t("enterprise.dlp.builtinRuleName"), dataIndex: "rule_name", key: "rule_name" },
    { title: t("enterprise.dlp.description"), dataIndex: "description", key: "description" },
    { title: t("enterprise.dlp.action"), dataIndex: "action", key: "action", render: renderActionTag },
    { title: t("enterprise.dlp.pattern"), dataIndex: "pattern_regex", key: "pattern_regex", render: (p: string) => <code>{p}</code> },
  ];

  const eventColumns = [
    { title: t("enterprise.dlp.triggeredAt"), dataIndex: "triggered_at", key: "triggered_at", render: (text: string) => new Date(text).toLocaleString() },
    { title: t("enterprise.dlp.rule"), dataIndex: "rule_name", key: "rule_name" },
    { title: t("enterprise.dlp.actionTaken"), dataIndex: "action_taken", key: "action_taken", render: renderActionTag },
    { title: t("enterprise.dlp.contextPath"), dataIndex: "context_path", key: "context_path" },
    { title: t("enterprise.dlp.contentSummary"), dataIndex: "content_summary", key: "content_summary" },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>{t("enterprise.dlp.title")}</h2>
        <Button
          type="primary"
          onClick={() => {
            setEditingRule(null);
            form.resetFields();
            setIsModalVisible(true);
          }}
        >
          {t("enterprise.dlp.createCustomRule")}
        </Button>
      </div>

      <Tabs defaultActiveKey="custom">
        <TabPane tab={t("enterprise.dlp.customRules")} key="custom">
          <Table columns={customRuleColumns} dataSource={rulesData?.items || []} rowKey="id" loading={rulesLoading} />
        </TabPane>
        <TabPane tab={t("enterprise.dlp.builtinRules")} key="builtin">
          <Table columns={builtinRuleColumns} dataSource={builtinRules || []} rowKey="rule_name" loading={builtinLoading} pagination={false} />
        </TabPane>
        <TabPane tab={t("enterprise.dlp.violationEvents")} key="events">
          <Table columns={eventColumns} dataSource={eventsData?.items || []} rowKey="id" loading={eventsLoading} />
        </TabPane>
      </Tabs>

      <Modal
        title={editingRule ? t("enterprise.dlp.editRule") : t("enterprise.dlp.createRule")}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
      >
        <Form form={form} layout="vertical" initialValues={{ action: "alert", is_active: true }}>
          <Form.Item name="rule_name" label={t("enterprise.dlp.ruleName")} rules={[{ required: true, message: t("enterprise.dlp.ruleNameRequired") }]}>
            <Input disabled={!!editingRule} />
          </Form.Item>
          <Form.Item name="description" label={t("enterprise.dlp.description")}>
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="pattern_regex" label={t("enterprise.dlp.regexPattern")} rules={[{ required: true, message: t("enterprise.dlp.regexPatternRequired") }]}>
            <Input />
          </Form.Item>
          <Form.Item name="action" label={t("enterprise.dlp.action")} rules={[{ required: true }]}>
            <Select>
              <Option value="mask">{t("enterprise.dlp.action.mask")}</Option>
              <Option value="alert">{t("enterprise.dlp.action.alert")}</Option>
              <Option value="block">{t("enterprise.dlp.action.block")}</Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_active" label={t("enterprise.dlp.status")} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DLPRules;
