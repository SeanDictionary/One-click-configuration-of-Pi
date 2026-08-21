# 一键配置 Pi

当你初次安装 [Pi](https://github.com/earendil-works/pi-coding-agent) 时，会发现缺少很多插件生态的支持，会特别难用，包括 Pi 自身的配置项。

## 使用方法

复制下面这段话发给 AI 即可，它会自动下载读取并按文档完成全部配置：

```
读取这篇文档，并按这篇文档内容进行配置
https://github.com/SeanDictionary/One-click-configuration-of-Pi/blob/main/pi%E9%85%8D%E7%BD%AE%E6%8C%87%E5%8D%97.md
```

---

## 它会做什么

Pi 会读取指南后，按 5 个阶段逐步执行：

1. **阶段 0 · 环境探测**：自动检测 OS、架构、HOME、是否已装 pi/gh/vscode、各 harness 的 skills 目录是否存在、`rpiv-ask-user-question` 是否已装。
2. **阶段 0.5 · 确保结构化提问工具可用**：未装时自动安装 `@juicesharp/rpiv-ask-user-question`，让后续访谈能用带选项/预览/多选的结构化提问。
3. **阶段 1 · 用户访谈（6 轮 25 问）**：分批多轮用 `ask_user_question` 询问，覆盖
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
4. **阶段 2 · 安装外部依赖**：按访谈结果跳过不用的，可能装 GitHub CLI、LSP server、VS Code。
5. **阶段 3 · 写入配置文件**：见下文清单。
6. **阶段 4 · 验证**：JSON 合法性校验、文件清单核对、重启 pi 自动安装扩展、provider 凭证配置。

---

## 当前包含的扩展（写入 `settings.json` 的 packages）

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

---

## 内置 Skills

本仓库 `skills/` 目录下提供可直接复用的 pi skill，每个子目录都是一个符合 [Agent Skills 标准](https://agentskills.io/specification) 的自包含 skill（含 `SKILL.md` + 脚本）。

| Skill | 作用 |
|---|---|
| [`migrate-claude-session-to-pi`](skills/migrate-claude-session-to-pi) | 把 Claude Code 会话（`~/.claude/projects/.../*.jsonl`）转换成可被 `pi --resume` 打开的 pi 会话；早期历史浓缩为摘要、近期对话完整保留，工具调用映射到 pi 工具，thinking 省略、结果截断。自动从 `~/.pi/agent/settings.json` 读取 provider/model。 |

### 安装内置 Skill

任选其一：

**方式 A · 复制到 pi 全局 skills 目录（推荐）**

```bash
cp -r skills/migrate-claude-session-to-pi ~/.pi/agent/skills/
```

复制后重启 pi（或在 pi 中执行 `/reload`），即可自动发现并加载，支持 `/skill:migrate-claude-session-to-pi` 调用。

**方式 B · 把本仓库 `skills/` 目录登记为 skills 源**

把仓库 clone 到本地后，在 `~/.pi/agent/settings.json` 的 `skills` 数组里加入该目录路径：

```json
{
  "skills": ["D:/Github/One-click-configuration-of-Pi/skills"]
}
```

pi 会递归发现该目录下所有含 `SKILL.md` 的子目录。

### 使用示例（迁移 Claude 会话）

```bash
python ~/.pi/agent/skills/migrate-claude-session-to-pi/claude2pi.py \
  "~/.claude/projects/<编码cwd>/<uuid>.jsonl" "<项目工作目录>" --cutoff "<ISO时间戳>"
```

- `--cutoff`：该时间点之后的回合完整保留为近期对话，之前的浓缩为一条结构化摘要；省略或传 `""` 则保留全部为近期对话。
- 完成后用 `cd <项目目录> && pi --resume` 选择迁移出的会话即可接续工作。

---

## 会写入的配置文件清单

所有文件位于 `~/.pi/` 下，路径跨平台（Windows / macOS / Linux）：

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

`fusion-models.json` 默认不创建，仅当用户明确要"模型融合"且能提供 ≥2 个 model id 时才生成。

---

## 特点

- **先访谈、后动手**：全部问完并复述确认，再改任何文件。
- **路径绝不硬编码**：能 `~` 就 `~`，必须绝对路径的才用你指定的值。
- **保留既有配置**：若设备已有 provider/model 等，只合并行为参数与 packages。
- **取舍清晰**：每个扩展、每个 LSP 语言、每个权限条目都严格按访谈结果增删。
- **跨平台**：一份指南通吃 Windows / macOS / Linux。

---

## 许可

本指南文档按 MIT 许可发布，可自由使用与修改。
