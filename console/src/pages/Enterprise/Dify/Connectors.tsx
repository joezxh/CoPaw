import React, { useState } from "react";
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
  const [form] = Form.useForm();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const { data: list, loading, refresh } = useRequest(difyConnectorsApi.list);

  const { run: createConnector, loading: createLoading } = useRequest(difyConnectorsApi.create, {
    manual: true,
    onSuccess: () => {
      message.success("Connector created successfully");
      setIsModalVisible(false);
      refresh();
    },
    onError: (e: any) => message.error(e?.response?.data?.detail || "Failed to create"),
  });

  const { run: updateConnector, loading: updateLoading } = useRequest(
    async (id: string, values: any) => await difyConnectorsApi.update(id, values),
    {
      manual: true,
      onSuccess: () => {
        message.success("Connector updated successfully");
        setIsModalVisible(false);
        refresh();
      },
      onError: (e: any) => message.error(e?.response?.data?.detail || "Failed to update"),
    }
  );

  const { run: deleteConnector } = useRequest(difyConnectorsApi.delete, {
    manual: true,
    onSuccess: () => {
      message.success("Connector deleted successfully");
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
      title: "Connector ID",
      dataIndex: "id",
      key: "id",
      render: (text: string) => (
        <Space>
          {text}
          <CopyOutlined
            onClick={() => {
              navigator.clipboard.writeText(text);
              message.success("ID coped to clipboard");
            }}
            style={{ cursor: "pointer", color: "#1890ff" }}
          />
        </Space>
      ),
    },
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "API URL",
      dataIndex: "api_url",
      key: "api_url",
    },
    {
      title: "Active",
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
      title: "Actions",
      key: "actions",
      render: (_: any, record: DifyConnector) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)} style={{ padding: 0 }}>
            Edit
          </Button>
          <Popconfirm
            title="Are you sure to delete this connector?"
            onConfirm={() => deleteConnector(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger style={{ padding: 0 }}>
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageContainer
      title="Dify Connectors"
      description="Manage external Dify workflow engine connectors. You can use these connector IDs with the `dify_workflow` Skill inside CoPaw agents."
      extra={[
        <Button key="create" type="primary" onClick={handleCreate}>
          Create Connector
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
        title={editingId ? "Edit Dify Connector" : "Create Dify Connector"}
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => setIsModalVisible(false)}
        confirmLoading={createLoading || updateLoading}
      >
        <Form form={form} layout="vertical" onFinish={onFinish} initialValues={{ is_active: true }}>
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: "Please input connector name!" }]}
          >
            <Input placeholder="e.g. Sales Report Dify Engine" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea placeholder="Internal description" />
          </Form.Item>
          <Form.Item
            name="api_url"
            label="API URL"
            rules={[{ required: true, message: "Please input API URL!" }]}
          >
            <Input placeholder="e.g. https://api.dify.ai/v1" />
          </Form.Item>
          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: true, message: "Please input API Key!" }]}
          >
            <Input.Password placeholder="App Secret Key from Dify" />
          </Form.Item>
          <Form.Item name="is_active" label="Status" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </PageContainer>
  );
};

export default DifyConnectors;
