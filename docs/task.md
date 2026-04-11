# CoPaw Enterprise — 实施任务清单

## Phase A — 核心安全加固

### A4. 用户组管理 API（无破坏性，优先上）
- [x] `app/routers/user_groups.py` — 用户组 CRUD + 成员管理
- [x] `console/src/api/modules/enterprise-groups.ts`
- [x] `console/src/pages/Enterprise/Groups/GroupList.tsx`

### A2. DLP 策略引擎（无破坏性）
- [x] `enterprise/dlp_service.py` — 正则规则 + mask/alert/block 策略
- [x] `db/models/dlp.py` — DLPRule / DLPEvent ORM
- [x] `app/routers/dlp.py` — 规则 CRUD + 事件查询
- [x] `enterprise/middleware.py` 集成 DLP 扫描
- [x] `console/src/api/modules/enterprise-dlp.ts`
- [x] `console/src/pages/Enterprise/Security/DLPRules.tsx`

### A3. 登录告警 & 异常检测（无破坏性）
- [x] `enterprise/alert_service.py` — Redis 计数 + 多通道通知
- [x] `db/models/alert.py` — AlertRule / AlertEvent ORM
- [x] `app/routers/alerts.py` — 规则 CRUD + 事件查询
- [x] `enterprise_auth.py` 集成登录失败告警
- [x] `console/src/api/modules/enterprise-alerts.ts`
- [x] `console/src/pages/Enterprise/Security/AlertRules.tsx`

### A1. 敏感字段加密（需迁移，最后执行）
- [x] `enterprise/crypto.py` — AES-256-GCM + EncryptedType
- [x] `db/models/user.py` mfa_secret 应用 EncryptedType
- [x] `alembic/versions/002_enterprise_phase_a.py`
- [x] `pyproject.toml` 添加 `cryptography` 依赖

## Phase B — Dify 深度集成（待执行）
- [ ] B1: Dify Connector 管理（模型 + 客户端 + 路由）
- [ ] B2: Dify 执行 + Webhook 回调
- [ ] B3: dify_workflow CoPaw Skill
- [ ] B4: 前端 Connector 页 + 工作流增强

## Phase C — 多租户 & 协作空间（待执行）
- [ ] C1: tenant_id 列迁移（所有核心模型 + Alembic）
- [ ] C2: OIDC SSO 连接器（authlib + Keycloak）
- [ ] C3: 协作空间 + Agent 共享

## Phase D — 生态建设（待执行）
- [ ] D1: 8 个企业预置 Skill
- [ ] D2: Skill 商店
- [ ] D3: Prometheus + Grafana 监控
