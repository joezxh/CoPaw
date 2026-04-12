---
name: dify_workflow
description: Use this skill to execute complex enterprise workflows running on Dify (e.g. data analysis, report generation, multi-step approval). You must obtain the connector ID and required inputs first. | 使用此技能来执行在 Dify 上运行的企业级复杂工作流（例如数据分析、报告生成、多步审批等）。必须先获取指定的 connector ID 和所需的输入变量。
metadata:
  builtin_skill_version: "1.0"
  copaw:
    emoji: "🚀"
---

# Dify Workflow (企业级工作流集成)

## 什么时候用

当你接收到的用户请求超出了基础技能的处理范围（例如要求执行非常复杂的审批流程、深度的数据分析、或者特定业务场景下的多步骤长文本生成），并且企业内部已经在 Dify 平台配置了相应的工作流时，**必须** 使用本技能。

### 应该使用
- 触发长时业务处理流程（如 "帮我生成华南区的月度销售总结报告"）
- 触发跨系统审批（如 "提交本次采购的审批请求"）
- 连接企业专有的知识库进行问答检索时（如果这个知识库被封装在 Dify 应用中）

### 不应使用
- 简单的闲聊对话
- 通过基础技能（如定时 cron, 发送消息）就能完成的简单任务
- 用户并没有指定或暗示使用复杂业务流

## 决策与执行规则

1. **先查询可用连接器:** 发送 `copaw dify list` 了解当前有哪些已经配好的 Dify Connector 可以使用。
2. **需要特定 ID:** `copaw dify run` 命令必须带 `--connector <ID>`。
3. **输入参数:** Dify工作流通常需要特定的 JSON 输入。你必须要求用户提供或者自己整理出需要的 JSON 字符串，并通过 `--inputs` 传递。
4. **用户标识:** 如果有必要，请通过 `--user` 指定请求用户的唯一标识（默认为 copaw-cli-user）。

---

## 常用命令

```bash
# 列出系统当前可用的 Dify Connector (包含 ID 和 状态)
copaw dify list

# 触发指定的 Dify 工作流
# 注意：--inputs 必须是一个合法的单行 JSON 字符串。如果在 bash 中执行，请注意双引号转义，例如：'{"key":"value"}'
copaw dify run \
  --connector "c2a12...93jd" \
  --inputs '{"purpose": "sales_report", "region": "South"}' \
  --user "alice"
```

## 最小工作流

1. 用户请求复杂业务处理（如“开始入职审批”）。
2. 执行 `copaw dify list` 查看是否有对应 Dify 连接器。
3. 如果需要参数但用户没给，先反问用户。
4. 构造完整正确的执行命令，执行 `copaw dify run --connector "xxx" --inputs '{"name":"Bob"}'`。
5. 等待并阅读返回的执行结果，将结果或最终状态概括回复给用户。

---

## 常见错误

### 错误 1：参数格式错误
`--inputs` 必须是标准的 JSON 格式！尽量在外面套单引号以免 bash 解析错误：`--inputs '{"key": "value"}'`。

### 错误 2：使用的 connector 不存在或未激活
执行 run 之前，务必先通过 `list` 命令确认其处于 Active 状态。
