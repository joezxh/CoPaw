import React, { useEffect, useState } from "react";
import { Table, Button, Space, Modal, Form, Input, message, Tag } from "antd";
import { useRequest } from "ahooks";
import {
  getGroups,
  createGroup,
  updateGroup,
  deleteGroup,
  UserGroup,
} from "../../../api/modules/enterprise-groups";

const GroupList: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingGroup, setEditingGroup] = useState<UserGroup | null>(null);
  const [form] = Form.useForm();

  const { data, loading, refresh } = useRequest(getGroups, {
    defaultParams: [{ offset: 0, limit: 50 }],
  });

  const handleEdit = (record: UserGroup) => {
    setEditingGroup(record);
    form.setFieldsValue(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    Modal.confirm({
      title: "Are you sure you want to delete this group?",
      onOk: async () => {
        try {
          await deleteGroup(id);
          message.success("Group deleted successfully");
          refresh();
        } catch (error: any) {
          message.error(error.message || "Failed to delete group");
        }
      },
    });
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      if (editingGroup) {
        await updateGroup(editingGroup.id, values);
        message.success("Group updated successfully");
      } else {
        await createGroup(values);
        message.success("Group created successfully");
      }
      setIsModalVisible(false);
      refresh();
    } catch (error: any) {
      if (error?.message) {
        message.error(error.message);
      }
    }
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
    setEditingGroup(null);
  };

  const columns = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "Created At",
      dataIndex: "created_at",
      key: "created_at",
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: any, record: UserGroup) => (
        <Space size="middle">
          <Button type="link" onClick={() => handleEdit(record)}>
            Edit
          </Button>
          <Button type="link" danger onClick={() => handleDelete(record.id)}>
            Delete
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
        <h2>User Groups</h2>
        <Button
          type="primary"
          onClick={() => {
            setEditingGroup(null);
            form.resetFields();
            setIsModalVisible(true);
          }}
        >
          Create Group
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={data?.items || []}
        rowKey="id"
        loading={loading}
        pagination={{ total: data?.total || 0, pageSize: 50 }}
      />

      <Modal
        title={editingGroup ? "Edit Group" : "Create Group"}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Group Name"
            rules={[{ required: true, message: "Please input the group name!" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GroupList;
