# Implementation Plan - Phase D: Ecosystem Building

This phase focuses on the "CoPaw Ecosystem," transforming the platform into a solution-rich environment with enterprise-ready skills, a distribution mechanism (Skill Store), and operational visibility (Monitoring).

## Proposed Changes

### 1. Enterprise Prebuilt Skills (D1)
I will create 8 high-quality enterprise skills in `src/copaw/agents/skills/`. Each skill consists of a `SKILL.md` with detailed instructions for the LLM.

- **[NEW]** `meeting_assistant`: Context-aware meeting summarization and action item tracking.
- **[NEW]** `report_generator`: Generates structured weekly/monthly reports from enterprise data.
- **[NEW]** `it_support_ticketing`: Standardized interface for creating and tracking IT support tickets.
- **[NEW]** `password_reset_helper`: Guided self-service for enterprise account recovery.
- **[NEW]** `hr_onboarding`: Automated onboarding checklist and knowledge retrieval for new hires.
- **[NEW]** `expense_approval`: Streamlined workflow for submitting and approving expense claims.
- **[NEW]** `invoice_ocr`: Extracts structured data from invoice images/PDFs.
- **[NEW]** `crm_sync`: Automated lead capture and synchronization with CRM systems (e.g., Salesforce).

### 2. Enterprise Skill Store (D2)
A centralized hub for discovering and deploying skills across the organization.

#### [NEW] `src/copaw/app/routers/skill_store.py`
- `GET /api/enterprise/skill-store`: Lists all available skills from the built-in pool and any custom published skills.
- `POST /api/enterprise/skill-store/install`: Installs a skill into a specific workspace/agent.

#### [NEW] `console/src/pages/Enterprise/Skills/SkillStore.tsx`
- A visual gallery of skills with search, filtering, and installation capabilities.
- Integrated into the Sidebar under the "Enterprise" section.

### 3. Monitoring & Observability (D3)
Implementing infrastructure for tracking system health and usage.

#### [MODIFY] `pyproject.toml`
- Add `prometheus-fastapi-instrumentator`.

#### [MODIFY] `src/copaw/app/main.py`
- Initialize the Prometheus instrumentator.
- Add custom metrics for `tenant_id` activity and skill invocation counts.

#### [NEW] `deploy/monitoring/grafana_dashboard.json`
- A pre-configured dashboard for visualizing enterprise metrics.

---

## User Review Required

> [!IMPORTANT]
> **Skills scripts:** Some skills (like `invoice_ocr` or `crm_sync`) might eventually need external API integrations or Python scripts. For this initial phase, I will focus on the **Frontmatter + Instructions** (`SKILL.md`) and basic logic. Do you have specific external tools/APIs you want these skills to use?

> [!NOTE]
> **Monitoring:** Prometheus will be exposed at `/metrics`. In a production environment, this should be protected by IP whitelisting or local-only access. I will implement it as a standard open metrics endpoint for now.

---

## Verification Plan

### Automated Tests
- `pytest tests/enterprise/test_skill_store.py`: Verify listing and installation logic.
- `pytest tests/enterprise/test_monitoring.py`: Verify `/metrics` returns valid Prometheus metrics.

### Manual Verification
- Navigate to the **Skill Store** in the console.
- Install the `meeting_assistant` skill to an agent.
- Confirm the agent can now use the skill in a chat.
- Access `/metrics` and confirm request counts and tenant labels are present.
