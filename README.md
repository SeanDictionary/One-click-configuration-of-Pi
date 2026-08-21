# 一键配置 Pi

当你初次安装 [Pi](https://github.com/earendil-works/pi-coding-agent) 时，会发现缺少很多插件生态的支持，会特别难用，包括 Pi 自身的配置项。本仓库提供两样东西：一份 pi 配置指南、若干可复用 skill，均可「复制一段话发给 AI」自动安装。

---

## 一、pi 配置指南

### 使用方法

复制下面这段话发给 AI 即可，它会自动下载读取并按文档完成全部配置：

```
读取这篇文档，并按这篇文档内容进行配置
https://github.com/SeanDictionary/One-click-configuration-of-Pi/blob/main/pi%E9%85%8D%E7%BD%AE%E6%8C%87%E5%8D%97.md
```

### 作用

AI 读取指南后会分阶段完成一次性的 pi 全套配置，先访谈、后动手，路径绝不硬编码、保留既有配置。涉及的全部内容如下：

- **阶段 0 · 环境探测（自动）**：检测 OS、架构、HOME、是否已装 pi/gh/vscode、各 harness 的 skills 目录是否存在、`rpiv-ask-user-question` 是否已装。
- **阶段 0.5 · 确保结构化提问工具可用**：未装时自动安装 `@juicesharp/rpiv-ask-user-question`，让后续访谈能用带选项/预览/多选的结构化提问。
- **阶段 1 · 用户访谈（6 轮 25 问）**，覆盖：
  - A · Provider 与模型
  - B · 路径（GitHub clone 缓存、npm 全局目录、Windows shellPath）
  - C · 外部工具（VS Code、gh、代理）
  - D · 搜索引擎（Exa / DuckDuckGo）
  - E · 抓取行为（是否自动开浏览器）
  - F · 扩展取舍（语音、rtk）
  - G · LSP 语言（TS/JS、Rust）
  - H · 并发与续轮（`maxConcurrent`、`continuationLimits`）
  - I · Skills 来源（复用 Claude Code / Codex / Cursor 等的 skills 目录）
  - J · 状态栏与权限模式（显示段、配色、密度、分隔符、截断、yoloMode、后台更新检查）
  - K · MCP 接入（自动导入 / 手动导入 / 不复用）
- **阶段 2 · 安装外部依赖**：按访谈结果跳过不用的，可能装 GitHub CLI、LSP server、VS Code。
- **阶段 3 · 写入配置文件**：见下文清单。
- **阶段 4 · 验证**：JSON 合法性校验、文件清单核对、重启 pi 自动安装扩展、provider 凭证配置。

**写入 `settings.json` 的 packages（扩展）**：

| 包名 | 作用 |
|---|---|
| `@gotgenes/pi-permission-system` | 权限系统（yoloMode / 白名单 / 危险命令拦截） |
| `@gotgenes/pi-subagents` | 子代理调度 |
| `@gotgenes/pi-subagents-worktrees` | 子代理 + worktree 协同 |
| `@juicesharp/rpiv-ask-user-question` | 结构化提问工具（访谈必备） |
| `@juicesharp/rpiv-i18n` | 多语言支持 |
| `@juicesharp/rpiv-todo` | 任务清单管理 |
| `@narumitw/pi-github-pr` | GitHub PR 操作 |
| `@narumitw/pi-goal` | goal 自动续轮 |
| `@narumitw/pi-lsp` | LSP 语言服务集成（TS / Rust） |
| `@narumitw/pi-plan-mode` | 计划模式 |
| `@narumitw/pi-statusline` | 可定制状态栏 |
| `@narumitw/pi-worktree` | git worktree 管理 |
| `pi-background-tasks` | 后台任务（带更新检查） |
| `pi-hermes-memory` | 持久记忆系统 |
| `pi-mcp-adapter` | MCP server 适配（可复用其他 harness 配置） |
| `pi-web-access` | 联网搜索 / 抓取 / YouTube / PDF |

可选扩展（按需追加）：`@juicesharp/rpiv-voice`（语音）、`pi-rtk-optimizer`（rtk 工具链）。

**会写入的配置文件清单**（均位于 `~/.pi/` 下，路径跨平台）：

| 文件 | 用途 |
|---|---|
| `~/.pi/agent/settings.json` | 主题、provider/model、shell、扩展 packages、skills 来源等 |
| `~/.pi/web-search.json` | 搜索/抓取路由、GitHub clone、代理、YouTube/PDF 等 |
| `~/.pi/agent/pi-statusline.json` | 状态栏显示段、配色、密度、截断 |
| `~/.pi/agent/pi-plan-mode.json` | 计划模式思考档、安全子命令 |
| `~/.pi/agent/pi-goal.json` | goal 续轮上限 |
| `~/.pi/agent/subagents.json` | 子代理并发数与轮次 |
| `~/.pi/agent/hermes-memory-config.json` | 持久记忆策略 |
| `~/.pi/agent/pi-lsp.json` | LSP server（仅当选了 TS/Rust） |
| `~/.pi/agent/extensions/pi-permission-system/config.json` | 权限白名单 / 黑名单 / yoloMode |
| `~/.pi/agent/mcp.json` | MCP 自动导入（仅当选 A 时创建） |

`fusion-models.json` 默认不创建，仅当用户明确要“模型融合”且能提供 ≥2 个 model id 时才生成。

---

## 二、内置 Skill

### 使用方法

复制下面这段话发给 AI 即可，它会读取 `SKILL.md` 并把 skill（`SKILL.md` + 同目录下的 `claude2pi.py`）下载安装到 `~/.pi/agent/skills/migrate-claude-session-to-pi/`：

```
安装这个 skill：读取它的 SKILL.md，并把 SKILL.md 与同目录下的 claude2pi.py 一起下载到 ~/.pi/agent/skills/migrate-claude-session-to-pi/，安装完成后简要告诉我它的用途与用法
https://github.com/SeanDictionary/One-click-configuration-of-Pi/blob/main/skills/migrate-claude-session-to-pi/SKILL.md
```

安装后重启 pi（或执行 `/reload`）即可自动发现并加载，支持 `/skill:migrate-claude-session-to-pi` 调用。本仓库 `skills/` 目录下每个子目录都是一个符合 [Agent Skills 标准](https://agentskills.io/specification) 的自包含 skill（含 `SKILL.md` + 脚本）。

### 作用

当前内置 [`migrate-claude-session-to-pi`](skills/migrate-claude-session-to-pi)：把 Claude Code 会话转换成可被 `pi --resume` 打开的 pi 会话。涉及的全部内容如下：

- **输入**：Claude Code 会话 JSONL（`~/.claude/projects/<编码cwd>/<uuid>.jsonl`）。
- **输出**：pi 会话 JSONL，写入 `~/.pi/agent/sessions/--<编码cwd>--/<ISO时间戳>_<uuid>.jsonl`，可用 `cd <项目目录> && pi --resume` 打开接续工作。
- **格式解析**：
  - Claude 每行是单个流式增量块；同 `message.id` 的多行组成一个助手回合，拼接 `text` 增量重建完整回复；每个 `tool_use` 块本身完整，按 id 与后续 `tool_result` 配对。
  - pi 会话：`session` 头 → `model_change` → `thinking_level_change` → `message`；`parentId` 形成严格线性链；助手消息带 `toolCall` 块，每条必须有一条匹配的 `toolResult`（按 id 1:1 配对，否则回放会断）。
- **内容处理**：
  - 早期历史浓缩为一条结构化摘要用户消息：AGENT.md 约定、用户需求时间线、涉及文件清单、关键进展摘要、最近状态。
  - 近期对话（`--cutoff` 指定时间点之后）完整保留：助手文本 + 工具调用 + 工具结果。
  - `thinking` 块全部省略以节省体积；每条工具结果截断到约 500 字符、近期助手文本截断到约 3000 字符。
  - 过滤 Claude 注入的噪音（`API Error`、`Please run /login`、余额不足、供应商熔断等），避免污染摘要。
- **工具映射**：`Read→read`、`Edit→edit`、`Write→write`、`Bash/PowerShell/Grep/Glob→bash`；`mcp__*`、`Skill`、`Agent` 等保留原名作为历史上下文（pi 不会重新执行）。
- **自动配置**：provider/model/thinking 从 `~/.pi/agent/settings.json` 自动读取，无需手填；可用 `--provider/--model/--thinking` 覆盖。
- **校验**：输出 0 坏 JSON、0 断链（parentId 全部指向已存在 id）、工具调用数 == 工具结果数、0 孤儿、`stopReason` 取值 ⊆ `{end_turn, toolUse}`。一个约 12 MB / 1 万行的会话典型压缩到约 175 KB。

---

## 许可

本指南与 skill 按 MIT 许可发布，可自由使用与修改。
