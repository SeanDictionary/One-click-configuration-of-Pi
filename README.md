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

### 会配置哪些内容（分部分）

指南先做环境探测 + 6 轮结构化访谈（provider/路径/工具/搜索/扩展/LSP/并发/skills/状态栏/权限/MCP），确认后再动手写文件，路径绝不硬编码、保留既有配置。配置内容按部分如下：

| 部分 | 文件 | 配什么 |
|---|---|---|
| **模型与 Provider** | `~/.pi/agent/models.json` | 自定义 provider（baseUrl/api/apiKey/compat/headers）+ 模型字段（id/contextWindow/maxTokens/thinkingLevelMap）+ **`cost` 费率**（美元/百万 token，不填则费用栏恒为 $0）。可选：AI 联网查官方定价自动填 |
| **Pi 核心** | `~/.pi/agent/settings.json` | 主题、defaultProvider/Model、shellPath、externalEditor、扩展 packages、skills 来源、compaction、retry、并发、续轮、思考档 |
| **联网** | `~/.pi/web-search.json` | 搜索/抓取路由、代理（ssrf）、GitHub clone 缓存、YouTube/PDF、autoOpenBrowser |
| **状态栏** | `~/.pi/agent/pi-statusline.json` 或 `~/.pi/agent/pi-starship.toml` | 二选一：**基础模式**（JSON 勾选段+配色/密度/分隔符/截断）或 **高级模式**（原生 starship TOML，`$变量`+`($style)` 自由排版+`$fill`右对齐+多行+阈值变色+两步流程[先布局后样式]） |
| **计划模式** | `~/.pi/agent/pi-plan-mode.json` | 思考档、计划期工具、safeSubcommands（git/gh 只读命令） |
| **goal 续轮** | `~/.pi/agent/pi-goal.json` | 续轮上限（automaticTurns/noProgressTurns） |
| **子代理** | `~/.pi/agent/subagents.json` | maxConcurrent、maxTurns、graceTurns、中断策略 |
| **持久记忆** | `~/.pi/agent/hermes-memory-config.json` | 记忆策略、容量上限、会话搜索、自动整合 |
| **LSP** | `~/.pi/agent/pi-lsp.json` | TS/JS、Rust 语言 server（按需，不写则不创建） |
| **权限** | `~/.pi/agent/extensions/pi-permission-system/config.json` 或 `~/.pi/agent/pi-auto-permissions/config.json` | 命令放行三选一：A 规则匹配（allow/ask/deny + yolo）/ B 模型语义判断 / C 不装（原生全放行） |
| **模型融合** | `~/.pi/agent/fusion-models.json` | 多候选并行+评分合并（可选，默认不创建） |
| **后台更新检查** | 环境变量 | `PI_BG_DISABLE_UPDATE_CHECK`（可选，默认开） |
| **MCP** | `~/.pi/agent/mcp.json` | 复用其他 harness 的 MCP server（可选，默认 off） |

### 涉及的扩展

| 包名 | 作用 | 安装 |
|---|---|---|
| `@gotgenes/pi-permission-system` 或 `@ogulcancelik/pi-auto-permissions` | 命令放行（二选一或都不装：A 规则匹配+yolo / B 模型语义判断 / C 原生全放行） | 按需（三选一） |
| `@gotgenes/pi-subagents` | 子代理调度 | 必装 |
| `@gotgenes/pi-subagents-worktrees` | 子代理 + worktree 协同 | 必装 |
| `@juicesharp/rpiv-ask-user-question` | 结构化提问工具（访谈必备） | 必装 |
| `@juicesharp/rpiv-i18n` | 多语言支持 | 必装 |
| `@juicesharp/rpiv-todo` | 任务清单管理 | 必装 |
| `@narumitw/pi-github-pr` | GitHub PR 操作 | 按需（用 gh 才装） |
| `@narumitw/pi-goal` | goal 自动续轮 | 必装 |
| `@narumitw/pi-lsp` | LSP 语言服务集成（TS / Rust） | 按需（写对应语言才装） |
| `@narumitw/pi-plan-mode` | 计划模式 | 必装 |
| `@narumitw/pi-statusline` 或 `@narumitw/pi-starship` | 可定制状态栏（二选一） | 按需（要定制状态栏就装一个） |
| `@narumitw/pi-worktree` | git worktree 管理 | 必装 |
| `pi-background-tasks` | 后台任务（带更新检查） | 必装 |
| `pi-hermes-memory` | 持久记忆系统 | 必装 |
| `pi-mcp-adapter` | MCP server 适配（可复用其他 harness 配置） | 必装 |
| `pi-web-access` | 联网搜索 / 抓取 / YouTube / PDF | 必装 |
| `@juicesharp/rpiv-voice` | 语音输入/输出 | 可选 |
| `pi-rtk-optimizer` | rtk 工具链 | 可选 |

---

## 二、内置 Skill

### 使用方法

复制下面这段话发给 AI 即可，它会扫描 `./skills` 目录、列出可选 skill、让你勾选要安装哪些，然后把选中的 skill（整个子目录，含 `SKILL.md` 及脚本）下载到 `~/.pi/agent/skills/` 下：

```
列出 skills 目录下所有 skill（每个含 SKILL.md 的子目录即一个 skill），让我选择要安装哪些，然后把选中的 skill 整个子目录下载到 ~/.pi/agent/skills/ 下，安装完成后简要告诉我各自的用途与用法
https://github.com/SeanDictionary/One-click-configuration-of-Pi/tree/main/skills
```

安装后重启 pi（或执行 `/reload`）即可自动发现并加载，可用 `/skill:<名称>` 调用。本仓库 `skills/` 目录下每个子目录都是一个符合 [Agent Skills 标准](https://agentskills.io/specification) 的自包含 skill（含 `SKILL.md` + 脚本）。

### 作用

| Skill 名称 | 主要功能 |
|---|---|
| [`migrate-claude-session-to-pi`](skills/migrate-claude-session-to-pi) | 把 Claude Code 会话 JSONL 转换成可被 `pi --resume` 打开的 pi 会话：早期历史浓缩为摘要、近期对话完整保留，工具调用映射到 pi 工具，thinking 省略、结果截断，provider/model 自动从 pi settings 读取。 |

---

## 许可

本指南与 skill 按 MIT 许可发布，可自由使用与修改。
