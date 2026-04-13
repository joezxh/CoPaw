import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Table,
  Button,
  Space,
  Popconfirm,
  message,
  Switch,
  Modal,
  Form,
  Input,
} from "antd";
import { useRequest } from "ahooks";
import { CopyOutlined } from "@ant-design/icons";
import { difyConnectorsApi, DifyConnector, DifyConnectorCreate } from "@/api/modules/enterprise-dify";
import PageContainer from "@/components/PageContainer";

const DifyConnectors: React.FC = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const { data: list, loading, refresh } = useRequest(difyConnectorsApi.list);

  const { run: createConnector, loading: createLoading } = useRequest(difyConnectorsApi.create, {
    manual: true,
    onSuccess: () => {
      message.success(t("enterprise.dify.createSuccess"));
      setIsModalVisible(false);
      refresh();
    },
    onError: (e: any) => message.error(e?.response?.data?.detail || t("enterprise.dify.createFailed")),
  });

  const { run: updateConnector, loading: updateLoading } = useRequest(
    async (id: string, values: any) => await difyConnectorsApi.update(id, values),
    {
      manual: true,
      onSuccess: () => {
        message.success(t("enterprise.dify.updateSuccess"));
        setIsModalVisible(false);
        refresh();
      },
      onError: (e: any) => message.error(e?.response?.data?.detail || t("enterprise.dify.updateFailed")),
    }
  );

  const { run: deleteConnector } = useRequest(difyConnectorsApi.delete, {
    manual: true,
    onSuccess: () => {
      message.success(t("enterprise.dify.deleteSuccess"));
      refresh();
    },
  });

  const handleCreate = () => {
    form.resetFields();
    setEditingId(null);
    setIsModalVisible(true);
  };

  const handleEdit = (record: DifyConnector) => {
    form.setFieldsValue({ ...record, api_key: "*********" });
    setEditingId(record.id);
    setIsModalVisible(true);
  };

  const onFinish = (values: any) => {
    // Note: If editing and user didn't change the dummy api key, strip it out so the backend doesn't overwrite it with '*********'
    if (editingId && values.api_key === "*********") {
      delete values.api_key;
      updateConnector(editingId, values);
    } else if (editingId) {
      updateConnector(editingId, values);
    } else {
      createConnector(values as DifyConnectorCreate);
    }
  };

  const columns = [
    {
      title: t("enterprise.dify.connectorId"),
      dataIndex: "id",
      key: "id",
      render: (text: string) => (
        <Space>
          {text}
          <CopyOutlined
            onClick={() => {
              navigator.clipboard.writeText(text);
              message.success(t("enterprise.dify.idCopied"));
            }}
            style={{ cursor: "pointer", color: "#1890ff" }}
          />
        </Space>
      ),
    },
    {
      title: t("enterprise.dify.name"),
      dataIndex: "name",
      key: "name",
    },
    {
      title: t("enterprise.dify.apiUrl"),
      dataIndex: "api_url",
      key: "api_url",
    },
    {
      title: t("enterprise.dify.active"),
      dataIndex: "is_active",
      key: "is_active",
      render: (isActive: boolean, record: DifyConnector) => (
        <Switch
          checked={isActive}
          onChange={(val) => updateConnector(record.id, { is_active: val })}
        />
      ),
    },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: any, record: DifyConnector) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)} style={{ padding: 0 }}>
            {t("common.edit")}
          </Button>
          <Popconfirm
            title={t("enterprise.dify.deleteConfirm")}
            onConfirm={() => deleteConnector(record.id)}
            okText={t("common.ok")}
            cancelText={t("common.cancel")}
          >
            <Button type="link" danger style={{ padding: 0 }}>
              {t("common.delete")}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageContainer
      title={t("enterprise.dify.title")}
      description={t("enterprise.dify.description")}
      extra={[
        <Button key="create" type="primary" onClick={handleCreate}>
          {t("enterprise.dify.createConnector")}
        </Button>,
      ]}
    >
      <Table
        rowKey="id"
        columns={columns}
        dataSource={list as DifyConnector[] | undefined}
        loading={loading}
        pagination={{ hideOnSinglePage: true }}
      />

      <Modal
        title={editingId ? t("enterprise.dify.editConnector") : t("enterprise.dify.createConnector")}
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={createLoading || updateLoading}
      >
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ is_active: true }}>
          <Form.Item
            name="name"
            label={t("enterprise.dify.name")}
            rules={[{ required: true, message: t("enterprise.dify.nameRequired") }]}
          >
            <Input placeholder={t("enterprise.dify.namePlaceholder")} />
          </Form.Item>
          <Form.Item name="description" label={t("enterprise.dify.description")}>
            <Input.TextArea placeholder={t("enterprise.dify.descriptionPlaceholder")} />
          </Form.Item>
          <Form.Item
            name="api_url"
            label={t("enterprise.dify.apiUrl")}
            rules={[{ required: true, message: t("enterprise.dify.apiUrlRequired") }]}
          >
            <Input placeholder={t("enterprise.dify.apiUrlPlaceholder")} />
          </Form.Item>
          <Form.Item
            name="api_key"
            label={t("enterprise.dify.apiKey")}
            rules={[{ required: true, message: t("enterprise.dify.apiKeyRequired") }]}
          >
            <Input.Password placeholder={t("enterprise.dify.apiKeyPlaceholder")} />
          </Form.Item>
          <Form.Item name="is_active" label={t("enterprise.dify.status")} valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
};

export default DifyConnectors;
