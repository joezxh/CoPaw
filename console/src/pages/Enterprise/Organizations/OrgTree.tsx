import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Tree, Button, Space, Modal, Form, Input, message, Drawer, Table, Tag, Popconfirm } from "antd";
import { useRequest } from "ahooks";
import {
  getOrgTree,
  createOrg,
  updateOrg,
  deleteOrg,
  getOrgMembers,
  addOrgMembers,
  removeOrgMember,
  getOrgStats,
  Organization,
  OrgMember,
  OrgStats as OrgStatsType,
} from "../../../api/modules/enterprise-orgs";
import {
  FolderAddOutlined,
  EditOutlined,
  DeleteOutlined,
  TeamOutlined,
  PlusOutlined,
} from "@ant-design/icons";

const OrgTree: React.FC = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [memberForm] = Form.useForm();
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [isMemberDrawerVisible, setIsMemberDrawerVisible] = useState(false);
  const [isAddMemberModalVisible, setIsAddMemberModalVisible] = useState(false);
  const [stats, setStats] = useState<OrgStatsType | null>(null);

  // Load organization tree
  const { data: treeData, loading, refresh } = useRequest(getOrgTree, {
    formatResult: (res) => convertToTreeData(res),
  });

  // Load members when drawer opens
  const { data: members, loading: membersLoading, refresh: refreshMembers } = useRequest(
    () => selectedOrg ? getOrgMembers(selectedOrg.id) : Promise.resolve([]),
    {
      ready: !!selectedOrg && isMemberDrawerVisible,
      refreshDeps: [selectedOrg?.id, isMemberDrawerVisible],
    }
  );

  // Convert API response to Ant Design Tree format
  const convertToTreeData = (orgs: Organization[]) => {
    const convert = (orgs: Organization[]) => {
      return orgs.map(org => ({
        key: org.id,
        title: (
          <Space>
            <span>{org.name}</span>
            <Tag color="blue">{org.level === 0 ? t("enterprise.orgs.rootOrg") : `L${org.level}`}</Tag>
          </Space>
        ),
        children: org.children ? convert(org.children) : [],
        org: org, // Store original org data
      }));
    };
    return convert(orgs);
  };

  const handleEdit = (org: Organization) => {
    setEditingOrg(org);
    form.setFieldsValue(org);
    setIsModalVisible(true);
  };

  const handleAddChild = (parentOrg: Organization) => {
    setEditingOrg(null);
    form.setFieldsValue({ parent_id: parentOrg.id });
    setIsModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteOrg(id);
      message.success(t("enterprise.orgs.deleteSuccess"));
      refresh();
    } catch (error: any) {
      if (error.status === 409) {
        message.error(t("enterprise.orgs.hasChildren"));
      } else {
        message.error(error.message || t("enterprise.orgs.deleteFailed"));
      }
    }
  };

  const handleViewMembers = async (org: Organization) => {
    setSelectedOrg(org);
    setIsMemberDrawerVisible(true);
    
    // Load stats
    try {
      const statsData = await getOrgStats(org.id);
      setStats(statsData);
    } catch (error) {
      console.error("Failed to load stats:", error);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingOrg) {
        await updateOrg(editingOrg.id, values);
        message.success(t("enterprise.orgs.updateSuccess"));
      } else {
        await createOrg(values);
        message.success(t("enterprise.orgs.createSuccess"));
      }
      setIsModalVisible(false);
      form.resetFields();
      refresh();
    } catch (error: any) {
      message.error(error.message || "Operation failed");
    }
  };

  const handleAddMembers = async () => {
    if (!selectedOrg) return;
    
    try {
      const values = await memberForm.validateFields();
      await addOrgMembers(selectedOrg.id, values.user_ids);
      message.success(t("enterprise.orgs.addMemberSuccess"));
      setIsAddMemberModalVisible(false);
      memberForm.resetFields();
      refreshMembers();
    } catch (error: any) {
      message.error(error.message || "Failed to add members");
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!selectedOrg) return;
    
    try {
      await removeOrgMember(selectedOrg.id, userId);
      message.success(t("enterprise.orgs.removeMemberSuccess"));
      refreshMembers();
    } catch (error: any) {
      message.error(error.message || "Failed to remove member");
    }
  };

  const memberColumns = [
    {
      title: t("enterprise.orgs.username"),
      dataIndex: "username",
      key: "username",
    },
    {
      title: t("enterprise.orgs.displayName"),
      dataIndex: "display_name",
      key: "display_name",
      render: (name: string) => name || "-",
    },
    {
      title: t("enterprise.orgs.email"),
      dataIndex: "email",
      key: "email",
    },
    {
      title: t("enterprise.orgs.status"),
      dataIndex: "status",
      key: "status",
      render: (status: string) => (
        <Tag color={status === "active" ? "green" : "red"}>
          {status}
        </Tag>
      ),
    },
    {
      title: t("common.actions"),
      key: "actions",
      render: (_: any, record: OrgMember) => (
        <Popconfirm
          title={t("enterprise.orgs.removeMemberConfirm")}
          onConfirm={() => handleRemoveMember(record.id)}
        >
          <Button type="link" danger size="small">
            {t("enterprise.orgs.removeMember")}
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
        <h2>{t("enterprise.orgs.title")}</h2>
        <Button 
          type="primary" 
          icon={<FolderAddOutlined />}
          onClick={() => {
            setEditingOrg(null);
            form.resetFields();
            setIsModalVisible(true);
          }}
        >
          {t("enterprise.orgs.addOrg")}
        </Button>
      </div>

      <Tree
        treeData={treeData}
        showLine
        selectable
        defaultExpandAll
        titleRender={(node: any) => (
          <Space>
            {node.title}
            <Space size="small" onClick={(e) => e.stopPropagation()}>
              <Button
                type="text"
                size="small"
                icon={<PlusOutlined />}
                onClick={() => handleAddChild(node.org)}
                title={t("enterprise.orgs.addSubOrg")}
              />
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleEdit(node.org)}
              />
              <Button
                type="text"
                size="small"
                icon={<TeamOutlined />}
                onClick={() => handleViewMembers(node.org)}
              />
              <Popconfirm
                title={t("enterprise.orgs.deleteConfirm")}
                onConfirm={() => handleDelete(node.org.id)}
              >
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Popconfirm>
            </Space>
          </Space>
        )}
      />

      {/* Create/Edit Modal */}
      <Modal
        title={editingOrg ? t("enterprise.orgs.editOrg") : t("enterprise.orgs.addOrg")}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label={t("enterprise.orgs.orgName")}
            rules={[{ required: true, message: t("enterprise.orgs.orgNameRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="parent_id" hidden>
            <Input />
          </Form.Item>
          <Form.Item name="manager_id" label={t("enterprise.orgs.manager")}>
            <Input placeholder="User ID" />
          </Form.Item>
          <Form.Item name="description" label={t("enterprise.orgs.description")}>
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Members Drawer */}
      <Drawer
        title={`${selectedOrg?.name} - ${t("enterprise.orgs.members")}`}
        placement="right"
        width={720}
        open={isMemberDrawerVisible}
        onClose={() => {
          setIsMemberDrawerVisible(false);
          setSelectedOrg(null);
          setStats(null);
        }}
      >
        {stats && (
          <Space style={{ marginBottom: 16 }}>
            <Tag color="blue">{t("enterprise.orgs.memberCount")}: {stats.member_count}</Tag>
            <Tag color="green">{t("enterprise.orgs.subOrgCount")}: {stats.sub_department_count}</Tag>
          </Space>
        )}
        
        <div style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setIsAddMemberModalVisible(true)}
          >
            {t("enterprise.orgs.addMember")}
          </Button>
        </div>

        <Table
          columns={memberColumns}
          dataSource={members}
          loading={membersLoading}
          rowKey="id"
          size="small"
        />
      </Drawer>

      {/* Add Members Modal */}
      <Modal
        title={t("enterprise.orgs.addMember")}
        open={isAddMemberModalVisible}
        onOk={handleAddMembers}
        onCancel={() => {
          setIsAddMemberModalVisible(false);
          memberForm.resetFields();
        }}
      >
        <Form form={memberForm} layout="vertical">
          <Form.Item
            name="user_ids"
            label={t("enterprise.orgs.userIds")}
            rules={[{ required: true, message: t("enterprise.orgs.userIdsRequired") }]}
          >
            <Input.TextArea 
              rows={4} 
              placeholder="Enter user IDs, one per line"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default OrgTree;
