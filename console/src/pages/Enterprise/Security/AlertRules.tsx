import React, { useState } from "react";
import { useTranslation } from "react-i18next";
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
  const { t } = useTranslation();
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
      title: t("enterprise.alerts.deleteConfirm"),
      onOk: async () => {
        try {
          await deleteAlertRule(id);
          message.success(t("enterprise.alerts.deleteSuccess"));
          refreshRules();
        } catch (error: any) {
          message.error(error.message || t("enterprise.alerts.deleteFailed"));
        }
      },
    });
  };

  const handleToggleStatus = async (id: string, is_active: boolean) => {
    try {
      await updateAlertRule(id, { is_active });
      message.success(t("enterprise.alerts.statusUpdated"));
      refreshRules();
    } catch (error: any) {
      message.error(error.message || t("enterprise.alerts.updateFailed"));
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingRule && editingRule.id) {
        await updateAlertRule(editingRule.id, values);
        message.success(t("enterprise.alerts.updateSuccess"));
      } else {
        await createAlertRule(values);
        message.success(t("enterprise.alerts.createSuccess"));
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
      await testNotification(t("enterprise.alerts.testMessage"));
      message.success(t("enterprise.alerts.testSuccess"));
      refreshEvents();
    } catch (error: any) {
      message.error(error.message || t("enterprise.alerts.testFailed"));
    }
  };

  const ruleColumns = [
    { title: t("enterprise.alerts.ruleType"), dataIndex: "rule_type", key: "rule_type" },
    { title: t("enterprise.alerts.description"), dataIndex: "description", key: "description" },
    { 
      title: t("enterprise.alerts.threshold"), 
      dataIndex: "threshold", 
      key: "threshold", 
      render: (threshold: number, r: AlertRule) => {
        // Use translation function from outer scope
        return t("enterprise.alerts.thresholdFormat", { count: threshold, window: r.window_seconds });
      }
    },
    { title: t("enterprise.alerts.channels"), dataIndex: "notify_channels", key: "notify_channels", render: (c: string[]) => c?.join(", ") || t("enterprise.alerts.none") },
    {
      title: t("enterprise.alerts.status"),
      key: "is_active",
      render: (_: any, record: AlertRule) => (
        <Switch checked={record.is_active} onChange={(checked) => handleToggleStatus(record.id, checked)} />
      ),
    },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: any, record: AlertRule) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)}>{t("common.edit")}</Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>{t("common.delete")}</Button>
        </Space>
      ),
    },
  ];

  const eventColumns = [
    { title: t("enterprise.alerts.triggeredAt"), dataIndex: "triggered_at", key: "triggered_at", render: (text: string) => new Date(text).toLocaleString() },
    { title: t("enterprise.alerts.ruleType"), dataIndex: "rule_type", key: "rule_type" },
    { title: t("enterprise.alerts.notifyStatus"), dataIndex: "notify_status", key: "notify_status" },
    { title: t("enterprise.alerts.context"), dataIndex: "context", key: "context", render: (c: any) => <pre style={{margin:0, fontSize:'12px'}}>{JSON.stringify(c, null, 2)}</pre> },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>{t("enterprise.alerts.title")}</h2>
        <Space>
          <Button onClick={handleTestNotification}>{t("enterprise.alerts.testNotification")}</Button>
          <Button type="primary" onClick={() => { setEditingRule(null); form.resetFields(); setIsModalVisible(true); }}>
            {t("enterprise.alerts.createAlertRule")}
          </Button>
        </Space>
      </div>

      <Tabs defaultActiveKey="rules">
        <TabPane tab={t("enterprise.alerts.alertRules")} key="rules">
          <Table columns={ruleColumns} dataSource={rulesData || []} rowKey="id" loading={rulesLoading} pagination={false} />
        </TabPane>
        <TabPane tab={t("enterprise.alerts.alertEvents")} key="events">
          <Table columns={eventColumns} dataSource={eventsData?.items || []} rowKey="id" loading={eventsLoading} />
        </TabPane>
      </Tabs>

      <Modal
        title={editingRule ? t("enterprise.alerts.editAlertRule") : t("enterprise.alerts.createAlertRule")}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText={t("common.ok")}
        cancelText={t("common.cancel")}
      >
        <Form form={form} layout="vertical" initialValues={{ threshold: 3, window_seconds: 300, is_active: true, notify_channels: [] }}>
          <Form.Item name="rule_type" label={t("enterprise.alerts.ruleType")} rules={[{ required: true, message: t("enterprise.alerts.ruleTypeRequired") }]}>
            <Input disabled={!!editingRule} />
          </Form.Item>
          <Form.Item name="description" label={t("enterprise.alerts.description")}>
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="threshold" label={t("enterprise.alerts.thresholdCount")} rules={[{ required: true, message: t("enterprise.alerts.thresholdCountRequired") }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="window_seconds" label={t("enterprise.alerts.timeWindow")} rules={[{ required: true, message: t("enterprise.alerts.timeWindowRequired") }]}>
            <InputNumber min={10} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notify_channels" label={t("enterprise.alerts.notificationChannels")}>
            <Select mode="tags" placeholder={t("enterprise.alerts.channelsPlaceholder")}>
              <Option value="wecom">{t("enterprise.alerts.channel.wecom")}</Option>
              <Option value="dingtalk">{t("enterprise.alerts.channel.dingtalk")}</Option>
              <Option value="email">{t("enterprise.alerts.channel.email")}</Option>
            </Select>
          </Form.Item>
          <Form.Item name="is_active" label={t("enterprise.alerts.status")} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AlertRules;
