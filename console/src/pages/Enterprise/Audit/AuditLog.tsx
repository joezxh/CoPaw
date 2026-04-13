import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Table, Tag, Select, DatePicker, Space, Switch,
  Typography, Tooltip
} from "antd";
import { SafetyOutlined } from "@ant-design/icons";
import { enterpriseAuditApi, AuditLogEntry } from "../../../api/modules/enterprise-audit";
import dayjs from "dayjs";

const { Title } = Typography;
const { RangePicker } = DatePicker;

const RESULT_COLOR: Record<string, string> = {
  success: "success",
  failure: "error",
  denied: "warning",
};

export default function AuditLog() {
  const { t } = useTranslation();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 50;

  const [actionFilter, setActionFilter] = useState<string | undefined>();
  const [resourceFilter, setResourceFilter] = useState<string | undefined>();
  const [resultFilter, setResultFilter] = useState<string | undefined>();
  const [sensitiveOnly, setSensitiveOnly] = useState(false);
  const [dateRange, setDateRange] = useState<[string, string] | undefined>();

  const load = async () => {
    setLoading(true);
    try {
      const res = await enterpriseAuditApi.query({
        action_type: actionFilter,
        resource_type: resourceFilter,
        result: resultFilter,
        is_sensitive: sensitiveOnly || undefined,
        from: dateRange?.[0],
        to: dateRange?.[1],
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setLogs(res.items);
      setTotal(res.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [actionFilter, resourceFilter, resultFilter, sensitiveOnly, dateRange, page]);

  const columns = [
    {
      title: t("enterprise.audit.timestamp"),
      dataIndex: "timestamp",
      key: "timestamp",
      width: 160,
      render: (v: string) => dayjs(v).format("MM/DD HH:mm:ss"),
    },
    { title: t("enterprise.audit.action"), dataIndex: "action_type", key: "action_type", width: 180, ellipsis: true },
    { title: t("enterprise.audit.resource"), dataIndex: "resource_type", key: "resource_type", width: 120 },
    {
      title: t("enterprise.audit.result"),
      dataIndex: "action_result",
      key: "action_result",
      width: 100,
      render: (r?: string) =>
        r ? <Tag color={RESULT_COLOR[r] ?? "default"}>{t(`enterprise.audit.result.${r}`, r)}</Tag> : "—",
    },
    { title: t("enterprise.audit.resourceId"), dataIndex: "resource_id", key: "resource_id", ellipsis: true },
    { title: t("enterprise.audit.userId"), dataIndex: "user_id", key: "user_id", ellipsis: true },
    { title: t("enterprise.audit.ip"), dataIndex: "client_ip", key: "client_ip", width: 130 },
    {
      title: t("enterprise.audit.sensitive"),
      dataIndex: "is_sensitive",
      key: "is_sensitive",
      width: 90,
      render: (v: boolean) =>
        v ? <Tooltip title={t("enterprise.audit.sensitiveOp")}><SafetyOutlined style={{ color: "#f5222d" }} /></Tooltip> : null,
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>{t("enterprise.audit.title")}</Title>
      </div>

      <Space wrap style={{ marginBottom: 16 }}>
        <Select
          placeholder={t("enterprise.audit.actionType")}
          allowClear
          style={{ width: 200 }}
          onChange={setActionFilter}
          options={[
            "USER_LOGIN", "USER_LOGOUT", "USER_REGISTER", "USER_CREATE",
            "USER_UPDATE", "USER_DISABLE", "PASSWORD_CHANGE", "MFA_ENABLE",
            "ROLE_CREATE", "ROLE_DELETE", "ROLE_ASSIGN", "PERMISSION_ASSIGN",
            "TASK_CREATE", "TASK_UPDATE", "TASK_DELETE", "TASK_STATUS_CHANGE",
            "WORKFLOW_CREATE", "WORKFLOW_RUN", "AGENT_RUN",
          ].map((a) => ({ label: t(`enterprise.audit.actions.${a}`, a), value: a }))}
        />
        <Select
          placeholder={t("enterprise.audit.resourceType")}
          allowClear
          style={{ width: 140 }}
          onChange={setResourceFilter}
          options={["user", "role", "task", "workflow", "agent"].map((r) => ({
            label: t(`enterprise.audit.resources.${r}`, r), value: r,
          }))}
        />
        <Select
          placeholder={t("enterprise.audit.result")}
          allowClear
          style={{ width: 120 }}
          onChange={setResultFilter}
          options={[
            { label: <Tag color="success">{t("enterprise.audit.result.success")}</Tag>, value: "success" },
            { label: <Tag color="error">{t("enterprise.audit.result.failure")}</Tag>, value: "failure" },
            { label: <Tag color="warning">{t("enterprise.audit.result.denied")}</Tag>, value: "denied" },
          ]}
        />
        <RangePicker
          showTime
          onChange={(_, s) => setDateRange(s[0] && s[1] ? [s[0], s[1]] : undefined)}
        />
        <Space>
          <span style={{ fontSize: 13 }}>{t("enterprise.audit.sensitiveOnly")}</span>
          <Switch size="small" checked={sensitiveOnly} onChange={setSensitiveOnly} />
        </Space>
      </Space>

      <Table
        columns={columns}
        dataSource={logs}
        rowKey="id"
        loading={loading}
        pagination={{ total, pageSize: PAGE_SIZE, current: page, onChange: setPage }}
        size="small"
        scroll={{ x: 1100 }}
      />
    </div>
  );
}
