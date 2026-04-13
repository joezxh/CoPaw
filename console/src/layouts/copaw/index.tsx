/**
 * Copaw Personal Layout
 * 
 * 个人版布局 - 不包含权限控制
 * 用于个人版 CoPaw（非企业版）
 */
import { Suspense, lazy } from "react";
import { Layout, Spin } from "antd";
import { Routes, Route, useLocation, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Sidebar from "./Sidebar";
import Header from "./Header";
import ConsoleCronBubble from "../../components/ConsoleCronBubble";
import { ChunkErrorBoundary } from "../../components/ChunkErrorBoundary";
import { lazyWithRetry } from "../../utils/lazyWithRetry";
import styles from "./index.module.less";

// Chat is eagerly loaded (default landing page)
import Chat from "../../pages/Chat";

// All other pages are lazily loaded with automatic retry on chunk failure
const ChannelsPage = lazyWithRetry(
  () => import("../../pages/Control/Channels"),
);
const SessionsPage = lazyWithRetry(
  () => import("../../pages/Control/Sessions"),
);
const CronJobsPage = lazyWithRetry(
  () => import("../../pages/Control/CronJobs"),
);
const HeartbeatPage = lazyWithRetry(
  () => import("../../pages/Control/Heartbeat"),
);
const AgentConfigPage = lazyWithRetry(() => import("../../pages/Agent/Config"));
const SkillsPage = lazyWithRetry(() => import("../../pages/Agent/Skills"));
const SkillPoolPage = lazyWithRetry(
  () => import("../../pages/Settings/SkillPool"),
);
const ToolsPage = lazyWithRetry(() => import("../../pages/Agent/Tools"));
const WorkspacePage = lazyWithRetry(
  () => import("../../pages/Agent/Workspace"),
);
const MCPPage = lazyWithRetry(() => import("../../pages/Agent/MCP"));
const ModelsPage = lazyWithRetry(() => import("../../pages/Settings/Models"));
const EnvironmentsPage = lazyWithRetry(
  () => import("../../pages/Settings/Environments"),
);
const SecurityPage = lazyWithRetry(
  () => import("../../pages/Settings/Security"),
);
const TokenUsagePage = lazyWithRetry(
  () => import("../../pages/Settings/TokenUsage"),
);
const VoiceTranscriptionPage = lazyWithRetry(
  () => import("../../pages/Settings/VoiceTranscription"),
);
const AgentsPage = lazyWithRetry(() => import("../../pages/Settings/Agents"));
const OrgTree = lazy(() => import("@/pages/Enterprise/Organizations/OrgTree"));
const DLPRules = lazy(() => import("@/pages/Enterprise/Security/DLPRules"));
const AlertRules = lazy(() => import("@/pages/Enterprise/Security/AlertRules"));
const DifyConnectors = lazy(() => import("@/pages/Enterprise/Dify/Connectors"));
const UserList = lazy(() => import("@/pages/Enterprise/Users/UserList"));
const RoleList = lazy(() => import("@/pages/Enterprise/Roles/RoleList"));
const WorkflowList = lazy(() => import("@/pages/Enterprise/Workflows/WorkflowList"));
const TaskBoard = lazy(() => import("@/pages/Enterprise/Tasks/TaskBoard"));
const AuditLog = lazy(() => import("@/pages/Enterprise/Audit/AuditLog"));

const { Content } = Layout;

const pathToKey: Record<string, string> = {
  "/chat": "chat",
  "/channels": "channels",
  "/sessions": "sessions",
  "/cron-jobs": "cron-jobs",
  "/heartbeat": "heartbeat",
  "/skills": "skills",
  "/skill-pool": "skill-pool",
  "/tools": "tools",
  "/mcp": "mcp",
  "/workspace": "workspace",
  "/agents": "agents",
  "/models": "models",
  "/environments": "environments",
  "/agent-config": "agent-config",
  "/security": "security",
  "/token-usage": "token-usage",
  "/voice-transcription": "voice-transcription",
  // Enterprise
  "/enterprise/users": "enterprise-users",
  "/enterprise/permissions": "enterprise-permissions",
  "/enterprise/organizations": "enterprise-orgs",
  "/enterprise/workflows": "enterprise-workflows",
  "/enterprise/tasks": "enterprise-tasks",
  "/enterprise/dlp-rules": "dlp-rules",
  "/enterprise/alert-rules": "alert-rules",
  "/enterprise/dify-connectors": "dify-connectors",
  "/enterprise/audit": "enterprise-audit",
};

export default function CopawLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const currentPath = location.pathname;
  const selectedKey = pathToKey[currentPath] || "chat";

  return (
    <Layout className={styles.mainLayout}>
      <Header />
      <Layout>
        <Sidebar selectedKey={selectedKey} />
        <Content className="page-container">
          <ConsoleCronBubble />
          <div className="page-content">
            <ChunkErrorBoundary resetKey={currentPath}>
              <Suspense
                fallback={
                  <Spin
                    tip={t("common.loading")}
                    style={{ display: "block", margin: "20vh auto" }}
                  >
                    <div />
                  </Spin>
                }
              >
                <Routes>
                  <Route path="/" element={<Navigate to="/chat" replace />} />
                  <Route path="/chat/*" element={<Chat />} />
                  <Route path="/channels" element={<ChannelsPage />} />
                  <Route path="/sessions" element={<SessionsPage />} />
                  <Route path="/cron-jobs" element={<CronJobsPage />} />
                  <Route path="/heartbeat" element={<HeartbeatPage />} />
                  <Route path="/skills" element={<SkillsPage />} />
                  <Route path="/skill-pool" element={<SkillPoolPage />} />
                  <Route path="/tools" element={<ToolsPage />} />
                  <Route path="/mcp" element={<MCPPage />} />
                  <Route path="/workspace" element={<WorkspacePage />} />
                  <Route path="/agents" element={<AgentsPage />} />
                  <Route path="/models" element={<ModelsPage />} />
                  <Route path="/environments" element={<EnvironmentsPage />} />
                  <Route path="/agent-config" element={<AgentConfigPage />} />
                  <Route path="/security" element={<SecurityPage />} />
                  <Route path="/token-usage" element={<TokenUsagePage />} />
                  <Route path="/voice-transcription" element={<VoiceTranscriptionPage />} />
                  <Route path="/enterprise/users" element={<UserList />} />
                  <Route path="/enterprise/permissions" element={<RoleList />} />
                  <Route path="/enterprise/organizations" element={<OrgTree />} />
                  <Route path="/enterprise/workflows" element={<WorkflowList />} />
                  <Route path="/enterprise/tasks" element={<TaskBoard />} />
                  <Route path="/enterprise/dlp-rules" element={<DLPRules />} />
                  <Route path="/enterprise/alert-rules" element={<AlertRules />} />
                  <Route path="/enterprise/dify-connectors" element={<DifyConnectors />} />
                  <Route path="/enterprise/audit" element={<AuditLog />} />
                </Routes>
              </Suspense>
            </ChunkErrorBoundary>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}
