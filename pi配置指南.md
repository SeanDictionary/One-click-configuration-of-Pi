# pi 个人配置 · 多设备迁移安装指南

> **这份文档的用途**：把这套统一的 pi 配置部署到任意新设备（Windows / macOS / Linux）。所有因设备、系统、个人习惯而异的项，**必须先询问用户再写入，绝不硬编码**。
>
> **执行者**：pi 编程助手（你）。请逐阶段执行，遇到"询问用户"的地方停下来等用户回答后再继续。
>
> **唯一传递物**：迁移时只传递本文件这一个 `.md`，不附带任何其他配置或决策文件。访谈得到的答案**只在当前会话内存中跟踪**（见附录 B 的记录表），**不落盘、不留档**；得到全部答案后直接询问用户"是否开始配置"，确认后立即按阶段 2/3 执行。

---

## 阶段 0：环境探测（自动，无需问用户）

执行以下命令收集环境信息，用于后续决策与路径替换：

```bash
echo "OS: $(uname -s)"; echo "ARCH: $(uname -m)"; echo "HOME: $HOME"; echo "USER: $USER"
node --version 2>/dev/null; npm --version 2>/dev/null
pi --version 2>/dev/null
gh --version 2>/dev/null && echo "gh: 已装" || echo "gh: 未装"
code --version 2>/dev/null && echo "vscode: 已装" || echo "vscode: 未装"
which bash
# 探测其他 agent harness 的 skills 目录是否存在（供阶段 1 问 I 用）
for d in ~/.claude/skills ~/.codex/skills ~/.agents/skills ~/.cursor/skills ~/.pi/agent/skills; do
  [ -d "$d" ] && echo "skills 源存在: $d" || echo "skills 源缺失: $d"
done
# 探测 models.json 是否已配 provider/model（供阶段 1 问 A1b 用）
[ -f "$HOME/.pi/agent/models.json" ] && echo "models.json: 已存在" || echo "models.json: 无"
# 探测 rpiv-ask-user-question 是否已安装（访谈要用的结构化提问工具）
if [ -d "~/.pi/agent/npm/node_modules/@juicesharp/rpiv-ask-user-question" ]; then
  echo "rpiv-ask-user-question: 已装"
else echo "rpiv-ask-user-question: 未装"; fi
```

记录结果：
- `OS` → `MINGW*`/`MSYS*` 视为 Windows（Git Bash）；`Darwin` = macOS；`Linux` = Linux
- `HOME` → 用户主目录，后续所有 `~` 都展开成它
- 判断 pi 是否已装、gh/vscode 是否已装
- **skills 源存在/缺失清单** → 直接用于阶段 1 问题 I，已存在的源作为可选项提示用户
- **rpiv-ask-user-question 是否已装** → 未装则先进阶段 0.5 安装它，再开始访谈
- **models.json 是否已存在** → 存在则在阶段 1 问 A1b（是否查官方定价更新 cost）

---

## 阶段 0.5：确保 rpiv-ask-user-question 已安装并生效

`@juicesharp/rpiv-ask-user-question` 提供 `ask_user_question` 工具，让阶段 1 的访谈能用**结构化提问**（带选项/预览/多选），比纯文本问答高效得多。**访谈前必须确保它已装且生效。**

### 判断方法
优先看 pi 当前会话是否能调用 `ask_user_question` 工具：
- 能调用 → 已生效，跳过本阶段，直接进阶段 1。
- 不能调用 → 按下面步骤安装。

（后台命令探测只是辅助：`~/.pi/agent/npm/node_modules/@juicesharp/rpiv-ask-user-question` 目录是否存在。以工具可用为准。）

### 安装步骤（未装时）

1. 读取现有 `<HOME>/.pi/agent/settings.json`（不存在则视为 `{}`）。
2. 确保 `packages` 数组里包含 `"npm:@juicesharp/rpiv-ask-user-question@2.4.0"`；若已有 `packages` 就追加这一项（去重），没有就新建。
3. 保留用户既有的 `defaultProvider`/`defaultModel`/`shellPath`/`theme` 等字段不动，只动 `packages`。
4. 写回 `settings.json`，用 `python -m json.tool` 校验合法。
5. **提示用户重启 pi**：
   > **建议**退出重进后--resume重新打开当前会话；如果新开对话，一定要**再次把这份指南交给 pi**
   > 请退出当前 pi 会话并重新打开（让 pi 重新读 settings.json 并 npm install 新扩展）。重启后它会检测到 `ask_user_question` 已可用，直接进入阶段 1 访谈。
6. 本轮执行到此停止，等用户重启。

### 重启后恢复
- pi 重启并重新接收本指南 → 重新跑阶段 0 → 阶段 0.5 检测到 `ask_user_question` 可用 → 直接进阶段 1。
- 阶段 1–4 照常进行。阶段 3.1 写 settings.json 时，`packages` 里会**保留**这个插件（已在清单中），不需重复添加。

> 说明：扩展加载需重启才生效，所以本阶段采用「装一次 → 重启 → 恢复」的模式，确保访谈时工具已在线。

---

## 阶段 1：用户访谈（分批多轮，用 ask_user_question 结构化提问）

**前提**：阶段 0.5 已确保 `ask_user_question` 工具可用。**优先用该工具**做结构化提问（带选项/预览/多选），用户也可自定义回答。

请**分批多轮询问**，不要一次性把所有问题抛出。按下面的分组逐轮问，每一轮问完等用户回答、确认后再进入下一轮。全部轮次完成后，汇总复述一次答案再进阶段 2。

**分轮策略（共 6 轮）**：
- **第 1 轮 · Provider 与路径**：A1 + B2 + B3 + B4（模型与几个必问路径，一次问完）
- **第 2 轮 · 外部工具与抓取偏好**：C5 + C6 + C7 + D8 + E9（编辑器/gh/代理/搜索/浏览器）
- **第 3 轮 · 扩展与语言取舍**：F10 + F11 + G12（语音/rtk/LSP 语言）
- **第 4 轮 · 性能与 Skills**：H13 + H14 + I15（并发/轮数/skills 源）
- **第 5 轮 · 状态栏与权限模式**：J16–J24（状态栏模式选择[基础/高级/不装] + 基础模式段/配色/密度/截断/上下文前缀/图标或高级模式 starship 模板 + 权限模式 + 后台更新检查）
- **第 6 轮 · MCP 接入**：K25（是否复用其他 harness 的 MCP 配置、用哪种方式）

> 每轮用 `ask_user_question` 结构化提问效果更佳；用户也可用自定义回答。轮次之间允许用户补充修改上一轮的答案。

### A. 模型与 Provider —— 属于第 1 轮
1. 你用哪个 LLM provider + model？（例如 dashscope+glm、deepseek、anthropic+claude 等）
   - 需要用户提供：`defaultProvider`、`defaultModel` 的值，以及 API key 配置方式（pi 的 `/provider` 或 auth.json）。
1b. **是否查官方定价并更新 `cost`**？（仅当阶段 0 探测到已有 `~/.pi/agent/models.json` 且含 provider+model 时才问）
    - 是 → AI 联网查厂商官方定价（美元/百万 token），写入各 model 的 `cost` 字段（见 3.2）。不查则 `cost` 留空，footer 费用栏恒为 `$0.000`。
    - 否 → 保留现状。

### B. 路径（必问，不能硬编码）—— 属于第 1 轮
2. **GitHub clone 缓存目录**？抓 GitHub 仓库时存哪？
   - 给默认建议：Windows `C:/Users/<USER>/AppData/Local/Temp/pi-github-repos`；macOS/Linux `/tmp/pi-github-repos`
   - 用户可自定义（本机作者用的是 `D:/Github/cache`）
3. **npm 全局 node_modules 目录**？用于 permission 白名单放行。
   - 检测：`npm root -g` 的输出。默认就采用它，让用户确认。
4. **shell 路径**（仅 Windows 必问）：Git Bash 的 bash.exe 路径？
   - 默认建议 `C:/Program Files/Git/bin/bash.exe`，让用户确认或改。
   - macOS/Linux 不需要 `shellPath` 字段。

### C. 外部工具与编辑器—— 属于第 2 轮
5. **是否用 VS Code** 作为外部编辑器？
   - 是 → `externalEditor: "code --wait"`
   - 否 → 不写该字段
6. **是否已装 / 是否要装 GitHub CLI (gh)**？
   - 用 GitHub 才需要。装了之后 pi-github-pr 扩展才有意义，pi-plan-mode 的 `safeSubcommands.gh` 才保留。
7. **网络是否走代理**（公司网 / VPN / 自建代理）？
   - 是 → `web-search.json` 的 `ssrf.trustEnvProxy: true`
   - 否 → `false`

### D. 搜索引擎 —— 属于第 2 轮
8. **是否有 Exa API key**？
   - 有 → `searchRouting.providers: ["exa", "duckduckgo"]`（需把 key 配到 pi-web-access 扩展）
   - 无 → `["duckduckgo"]`（无需 key）

### E. 抓取行为偏好 —— 属于第 2 轮
9. **抓完网页内容是否自动打开浏览器**？
   - 是 → `autoOpenBrowser: true`
   - 否 → `false`

### F. 扩展取舍 —— 属于第 3 轮
10. **是否需要语音输入/输出**？（`@juicesharp/rpiv-voice`）
    - 不需要 → 从 packages 删除（默认不装）
11. **是否使用 rtk 工具链**？（`pi-rtk-optimizer`）
    - 默认不装。仅当用户明确说在用 rtk 时才装，并在 permission 配置里加回 rtk 命令条目。

### G. LSP 语言—— 属于第 3 轮
12. **日常写哪些语言**？（决定 `pi-lsp.json` 配几个 server + 装哪个 LSP）
    - TypeScript/JS → 保留 typescript 段，需 `npm i -g typescript-language-server typescript`
    - Rust → 保留 rust-analyzer 段，需 `rustup component add rust-analyzer`
    - 都不写 → 不创建 pi-lsp.json，且从 packages 删 `@narumitw/pi-lsp`

### H. 并发与轮次（性能/预算相关）—— 属于第 4 轮
13. **子代理并发数** `maxConcurrent`？
    - 默认 `4`。机器弱或省钱 → `2`；机器强 + 预算足 → `6`
14. **goal 自动续轮** `continuationLimits`？
    - 默认推荐 `automaticTurns: 20, noProgressTurns: 5`（偏激进）
    - 保守：`12 / 3`；极激进：`30 / 8`

### I. Skills 来源（跨 harness 复用）—— 属于第 4 轮
15. **从哪些来源加载 skills**？pi 原生支持把其他 agent harness（Claude Code / Codex / Cursor 等）的 skills 目录接进来，无需软链接、无需拷贝。
    - 常见可选源：
      - `~/.claude/skills`（Claude Code）
      - `~/.codex/skills`（OpenAI Codex）
      - `~/.agents/skills`（通用 Agent Skills 标准）
      - `~/.cursor/skills`（Cursor）
      - `~/.pi/agent/skills`（pi 自带全局目录，本机若用则可一并放进去）
    - **把阶段 0 探测到的“skills 源存在”清单提示给用户**，让用户勾选要复用哪几个；不勾选的就不写进配置。
    - 用户也可自定义额外路径（绝对路径或 `~` 开头）。
    - 勾选结果填入 settings.json 的 `skills` 数组（见 3.1）。
    - 默认建议：只要存在的 `.claude/skills` 都勾上（最常用的复用场景）。

### J. 状态栏与权限模式（第 5 轮，高度可自定义）

16. **状态栏模式**？先让用户在下面三种里选一种（决定 J17–J22 是否继续问、写哪个配置文件、装哪个扩展）。**默认：基础模式**——不确定或不想折腾就选基础，足够日常使用；高级模式留给想要逐段控制颜色/排版/右对齐/多行的人。
    - **基础模式（pi-statusline）**（默认）：JSON 配置，勾选要显示的段、选配色/密度/分隔符/截断。简单、够用。→ 继续问 J17–J22，最终写 `pi-statusline.json`。
    - **高级模式（pi-starship）**：原生 Starship TOML，用 `$变量` + `($style)` 自由排版，支持 `$fill` 右对齐、多行、阈值变色、全套模块。高度自定义。→ **跳过 J17–J22**，改走本问末尾的「高级模板流程」，最终写 `pi-starship.toml`。
    - **不装**：用 pi 内置状态栏。→ packages 不加 statusline/starship，不写配置文件，跳过 J17–J22。
    > 基础与高级二选一，不能同时装（两个扩展都独占 footer）。切换时先 `pi remove` 旧扩展再 `pi install` 新扩展。

    **（仅基础模式）状态栏显示哪些段**？先把「全开」的样子给用户看，再让用户勾选要保留的段。
    - 全开示例（pi-statusline 第一行，从左到右）：
      ```
      ░▒▓ 🤖 <模型名> • 🧠 <思考档> • 📁 <当前目录> • 🌿 <git分支或no-git> • ctx <上下文已用%>/<总窗口> • 📦 <保留缓存> CH<命中率%> • 💸 <累计花费>
      ```
    - 可选段（逐项说明，让用户勾选）：
      | 段 | 显示内容 | 含义 |
      |---|---|---|
      | `model` | `🤖 glm-5.2` | 当前模型名（超长可截断） |
      | `thinking` | `🧠 medium` | 当前思考档（off/low/medium/high/max） |
      | `cwd` | `📁 ~` | 当前工作目录 |
      | `branch` | `🌿 main` 或 `🌿 no-git` | git 分支，非仓库显示 no-git |
      | `context` | `ctx 8.1%/1.0m` | 上下文已用比例 + 总窗口 token 数 |
      | `cache` | `📦 R4.1m CH99.5%` | 保留缓存 token + 命中率 |
      | `cost` | `💸 $0.05` | 本次会话累计花费 |
    - 默认建议：全开（7 段都保留）。用户可任意子集。

    **（仅高级模式）高级模板流程**：选了高级模式后，分两步走，**前一步定下的模块集合在后一步必须原样继承、不增删不改序**：
    - **步骤 1 · 内容与布局**：先确定显示哪些模块、什么顺序、是否 `$fill` 右对齐、是否多行 → 得到根 `format`。AI 记录这一步选定的模块集合。
    - **步骤 2 · 显示样式**：对步骤 1 定下的那批模块逐个定颜色/字重/背景/阈值变色 → 得到各 `[模块]` 表。**严禁在步骤 2 增删模块或改顺序**——样式只作用于步骤 1 的布局。
    下面先给可用变量表（供步骤 1 选模块），再给两步的语法。不再逐项问 J17–J22。
    - **可用变量（全套）**：
      | 模块 | 变量 | 含义 |
      |---|---|---|
      | `brand` | `$symbol` | Pi 品牌标记 |
      | `provider` | `$symbol` `$provider` | 当前 provider 名 |
      | `model` | `$symbol` `$model` | 当前模型名（可截断） |
      | `thinking` | `$symbol` `$level` | 思考档（off/minimal/low/medium/high/xhigh/max） |
      | `directory` | `$symbol` `$path` `$full_path` | 当前目录 |
      | `git_branch` | `$symbol` `$branch` `$remote_name` `$remote_branch` | git 分支 |
      | `git_status` | `$symbol` `$all_status` `$ahead` `$behind` `$modified` `$untracked` `$staged` `$conflicted` … | git 状态计数 |
      | `git_commit` | `$symbol` `$hash` `$tag` | HEAD 短哈希 + tag |
      | `activity` | `$symbol` `$state` `$tool` `$count` `$text` | 活动工具/流式/空闲 |
      | `context` | `$symbol` `$percentage` `$tokens` `$window` | 上下文已用% + 窗口 |
      | `tokens` | `$symbol` `$input` `$output` `$total` | 累计输入/输出 token |
      | `cache` | `$symbol` `$rate` `$read` `$write` | 缓存命中率 + 读/写 token（默认禁用，需 `disabled=false`） |
      | `cost` | `$symbol` `$cost` `$subscription` | 累计花费 + (sub) 标记 |
      | `time` | `$symbol` `$time` | 本地时间 |
      | `turn` | `$symbol` `$count` | 用户轮次 |
      | `fill` | `$symbol` | 撑开空白做右对齐布局 |
      | `extension_status` | `$symbol` `$statuses` `$count` | 其他扩展状态 |
      > 其余模块（package/nodejs/python/rust/golang/docker_context/kubernetes/aws/gcloud/azure/os/container/hostname/username 等）按需查 pi-starship 文档。
    - **步骤 1 · 内容与布局语法**（先定模块和顺序，AI 记下这个模块集合传给步骤 2）：
      - 根 `format` 是若干 `$模块` 顺序拼成的字符串；模块按出现顺序渲染。
      - `$fill` 把其后内容顶到行尾（右对齐）。多行：在 `format` 里直接换行（TOML 多行字符串）。
      - 模块默认格式可被 `[模块]` 表覆盖：`format`、`symbol`、`disabled`、`style`，以及模块选项（如 model 的 `truncation_length`/`truncation_symbol`/`truncation_direction`）。
      - `cache` 默认 `disabled=true`，要用得加 `[cache]` 表设 `disabled = false`。
    - **步骤 2 · 显示样式**（基于步骤 1 的模块集合，只改色/字重/背景，不动模块和顺序——这是高级模式区别于基础模式的核心）：
      - **继承约束**：步骤 2 的 `[模块]` 表必须与步骤 1 `format` 里的模块一一对应；不得新增步骤 1 没有的模块、不得删除、不得改顺序。样式是给步骤 1 的布局上色，不是重新布局。
      - **整段样式**：每个 `[模块]` 表里写 `style = "..."`，作用于该模块 `format` 里 `($style)` 组包住的整段文字。例：`[model]\nstyle = "bold blue"`。
      - **行内分段样式**：在模块 `format` 里用多个 `($style)` 组给一段文字内的不同部分上不同色。例：`format = "[$model ](bold blue)[$cost](bold red)"`——同一段里模型蓝、花费红。
      - **样式 token**（空格分隔，后写覆盖前写）：`bold` / `dim` / `italic` / `underline` / 颜色名（`red`/`green`/`blue`/`yellow`/`cyan`/`purple`/`white`/`bright-red`…）/ `fg:#RRGGBB`（前景）/ `bg:#RRGGBB`（背景）/ `prev_fg`（继承上一段前景色）/ `prev_bg`（继承上一段背景色）。例：`"fg:#e3e5e5 bg:#769ff0"`、`"bold bright-yellow"`。
      - **调色板**：顶部 `palette = "mine"` + `[palettes.mine]` 表自定义颜色名别名（如 `blue = "#86BBD8"`），之后 style 里就能用 `blue` 引用你的色。无内置调色板，不自定义则用终端原色。
      - **阈值变色**（context/cost 独有）：用 `[[context.display]]` / `[[cost.display]]` 给 `threshold`/`style`/`hidden` 三元组，按当前值命中「最高 threshold 且 ≤ 当前值」的那条样式。默认 `context` 0% 隐藏、30 绿/60 黄/80 红；`cost` 0 隐藏、1 黄/5 红。想让 0 也显示就把 threshold=0 的 `hidden` 改 false；想加更多档（如 50% 橙）就加一条 `[[context.display]]`。
      - **相邻同色合并**：相邻段背景色相同时自动合并成一个色块，过渡用 powerline 符号衔接——给多段设相同 `bg:#...` 就能拼出连贯色条。
      - **背景色铺满行为**（取决于布局，设了 `bg:` 才需要考虑）：
        - **双侧布局（format 含 `$fill`）**：背景自动铺满全行——给 `[fill]` 设与各段相同的 `bg:#...`，`$fill` 撑开的空白就带背景，左右两块连成一整条。无需问用户。
        - **单侧布局（format 无 `$fill`）**：背景只在有文字的段出现，行尾留空。**必须问用户**：“背景铺满全行”还是“只随文字出现”。选“铺满”→ 在 format 末尾追加 `$fill` 并给 `[fill]` 设 `bg:#...`；选“只随文字”→ 不加 fill，各段背景各自为块。
      - **能力边界（做不到的，别硬试）**：
        - `cache` 模块**无阈值变色机制**（只有 format/symbol/style/disabled，没有 `display`）——`[[cache.display]]` 会被当未知字段忽略，命中率**只能整段一个色**，不能按 0-70/70-90 分档变色。
        - `git_branch` 模块**无状态色机制**——要按 git 状态（ahead/behind/modified/untracked）变色，必须改用 `git_status` 模块（行内分段 `[$ahead](green)[$behind](red)[$modified](yellow)[$untracked](cyan)`，状态不命中时变量为空、该组不渲染）。这会改步骤1的模块集合，需回步骤1加 `git_status`。
      - **Nerd Font 前置**：powerline 色块过渡符、相邻同色合并的衔接符需要 **Nerd Font** 字体。没装则色块仍生效但过渡处缺箭头（显示为方框或空白），不是配置坏了。基础模式的 dot/bar 分隔符无需 Nerd Font。
    > 基础模式只能从 7 个预设调色板里选一个 + 截断；高级模式能逐段、逐行内片段、逐阈值地控色，这是两者最大的能力差。
    - **示例模板**（用户可照此改，渲染约：` 📁 ~ 🌿 no-git 📊 6.7%/1.0m 94.5%/1.9m 💸 $0.000          cannbot-dashscope · 🤖 glm-5.2 high`）：
      ```toml
      format = """
      $directory$git_branch$context$cache$cost\
      $fill\
      $provider$model$thinking"""

      [model]
      format = "[$symbol $model]($style)"
      symbol = "🤖"
      style = "bold blue"
      truncation_length = 40
      truncation_symbol = "…"
      truncation_direction = "middle"

      [provider]
      format = "[$provider · ]($style)"
      symbol = ""
      style = "bold blue"

      [thinking]
      format = "[ $level]($style)"
      symbol = ""
      style = "bold purple"

      [directory]
      format = "[ $symbol $path]($style)"
      symbol = "📁"
      style = "cyan bold"

      [git_branch]
      format = "[ $symbol $branch]($style)"
      symbol = "🌿"
      style = "bold purple"

      [context]
      format = "[ $symbol $percentage/$window]($style)"
      symbol = "📊"
      [[context.display]]
      threshold = 0
      style = "bold green"
      hidden = false
      [[context.display]]
      threshold = 70
      style = "bold yellow"
      hidden = false
      [[context.display]]
      threshold = 90
      style = "bold red"
      hidden = false

      [cache]
      disabled = false
      format = "[ $rate/$read]($style)"
      symbol = ""
      style = "bold green"

      [cost]
      symbol = "💸"
      [[cost.display]]
      threshold = 0
      style = "bold green"
      hidden = false
      [[cost.display]]
      threshold = 1
      style = "bold yellow"
      hidden = false
      [[cost.display]]
      threshold = 5
      style = "bold red"
      hidden = false
      ```
    - **AI 生成规则**：
      - **两步一致性**：若用户分两步给（先 format 后样式），步骤 2 的 `[模块]` 表必须与步骤 1 的 `format` 模块集合完全一致；AI 自动校对，发现步骤 2 多写/漏写/改序的模块要以步骤 1 为准回退并提示用户。
      - 用户给的模板若已含 `[模块]` 表 → 原样写入 `pi-starship.toml`，只补必要缺失项（如 `[[cost.display]]` 的 threshold=0 不隐藏），并校验 `[模块]` 与 `format` 模块一致。
      - **背景色铺满**：若用户设了 `bg:` 且 format 含 `$fill`（双侧）→ 自动给 `[fill]` 设同色 `bg:`，背景铺满全行，不用问；若 format 不含 `$fill`（单侧）→ 先问用户“铺满全行 / 只随文字”，按答案决定是否末尾加 `$fill`+`bg:`。
      - 用户若只给了一行 `format` 字符串 → AI 按上面示例的默认 `[模块]` 表补齐（步骤 1 的模块集合决定要补哪些 `[模块]` 表），symbol/style 用合理默认。
      - 写完后用 `smol-toml`（或 `pi -e npm:@narumitw/pi-starship` 加载后 `/starship status`）校验语法；无效字段会被 pi-starship 警告并忽略。
      - 用户可事后用 `/starship` → Customize footer 交互调优。
    > J17–J22 仅在「基础模式」时提问；高级模式直接跳到 J23。
17. **配色板 `palettePreset`**？
    - 常见值：`ocean`（冷蓝绿，默认）/`dark`/`light`/`solarized`。让用户选，不确定则 `ocean`。
18. **密度 `density`**？
    - `compact`（紧凑，默认）/`normal`/`comfortable`。让用户选。
19. **段分隔符 `separator`**？
    - `dot`（点·，默认）/`bar`（竖线│）/`none` 等。让用户选。
20. **模型名截断**？
    - 是否启用：`true`（默认）/`false`（不截断）
    - 截断长度：默认 `40`；可改（如 20 更短、60 更长）
    - 截断方向：`middle`（中间 `…`，默认）/`end`
21. **上下文段前缀/后缀**？
    - 默认 `prefix: "ctx "`、`suffix: ""`。让用户自定义文字，或保持默认。
22. **扩展状态图标 `extensionStatusIcons`**？
    - 默认 `goal: ◎`、`mcp:*: ◈`。让用户自定义 emoji/字符，或保持默认，或删掉该段。
23. **命令放行插件**？三选一（严格互斥，决定装哪个扩展、写哪个配置、后续问什么）：
    - **A. `@gotgenes/pi-permission-system`（规则匹配，默认推荐）**：用 allow/ask/deny 规则逐条匹配命令（glob，last-match-wins），无匹配默认 `ask`。也管 path（跨工具横切，防 symlink 绕过）/external_directory/mcp/skill。零模型开销。可叠加 yoloMode 把所有 `ask` 自动放行（仅显式 `deny` + fail-closed 拦）。→ 选 A 后再问 J23b（yoloMode 开/关）。
    - **B. `@ogulcancelik/pi-auto-permissions`（模型语义判断）**：守护模型读会话上下文逐条判断——用户在对话里授权过的命令自动放行、违反约束的拦、未明确授权的弹人工、高风险永远要确认。**只管 bash**（不管 path/external_directory）；每条 guarded 命令一次模型调用（有成本/延迟）。→ 选 B 后再问 J23b（reviewer 用哪个 provider/model + 哪些命令设 guarded）。
    - **C. 不装**：pi 原生行为——**所有 bash/文件操作直接执行，无任何确认**（pi 不含内置 permission popups）。⚠️ 这是**最不安全**的（连 yolo 的 deny 兜底都没有），不是“每次问”；仅适合完全可信的隔离环境。
    > A 与 B 严格二选一（都 gate bash，同装会双重弹窗）。默认建议 A（本地开发，规则 + deny 兜底 + 可选 yolo）。
23b. **（J23=A 时）yoloMode 开/关**？
    - 开：未匹配命令自动放行（仅 deny 拦），状态栏显示 `🔌 yolo`。打扰最少。
    - 关：未匹配命令弹人工（双击确认），更安全但烦。
    - 默认建议：本地开发选开，重要/共享机器选关。
    **（J23=B 时）auto-permissions 配置**：
    - reviewer 用哪个 provider/model（建议用低价 model，如 cannbot glm-5.2 或 flash）+ `reasoningEffort`/`timeoutMs`
    - 哪些命令设 `guarded`（模型审）vs `convention`（直接拦）——通常危险动作（commit/push/publish/rm 等）设 guarded，约定违规设 convention
    **（J23=C 时）**：无后续问题，不写配置文件。
24. **后台任务更新检查**？（pi-background-tasks 第二行右边的 `🔌 bg ⬆ vX /bg-update`）
    - `开`（默认，会检测新版本并提示 `/bg-update`）
    - `关`（设环境变量 `PI_BG_DISABLE_UPDATE_CHECK=1`，footer 不再显示更新段；`PI_OFFLINE=1` 也会连带关闭）
    - 让用户选。默认建议开（能及时知道有更新）。

### K. MCP 接入（第 6 轮）

25. **是否复用其他 harness 已配的 MCP server**？pi-mcp-adapter 能从 Claude Code / Codex / Cursor / Windsurf / VS Code / opencode 等的 MCP 配置里读取 server，避免重复配置。但**默认是关的**（`hostConfigDiscovery: "off"`），需要用户选一种接入方式：

    | 方式 | 做法 | 特点 |
    |---|---|---|
    | **A. 自动导入（推荐）** | 在 `~/.pi/agent/mcp.json` 写 `{"settings":{"hostConfigDiscovery":"on"}}` | pi 启动时自动把所有 harness 的 MCP server 作为最低优先级加载，零打扰；以后增删自动同步；只读不改外部配置 |
    | B. 手动逐个导入 | 在 pi 里跑 `/mcp setup` 交互选 | 挑要导入的 server，写进 pi 自己的 mcp.json；适合只想要其中几个 |
    | C. CLI 一次性发现 | `pi-mcp-adapter init --discover-host-configs` | 命令行版手动导入 |
    | D. 不复用 | `hostConfigDiscovery` 保持 `"off"`，不写 mcp.json | 用户想全部手动在 pi 里重配 |

    - **pi 能自动读的路径**（仅当 A 开启时）：`~/.claude.json`、`~/.claude/mcp.json`、`~/.claude/claude_desktop_config.json`（Claude Code）；`~/.codex/config.toml`、`~/.codex/config.json`（Codex）；`~/.cursor/mcp.json`；`~/.windsurf/mcp.json`；`./.vscode/mcp.json`（项目级）；`~/.config/opencode/opencode.json`；以及通用标准 `~/.config/mcp/mcp.json`、`~/.agents/mcp.json`。
    - **默认推荐 A**：零配置同步、跨 harness 共用、不改外部文件。仅当用户明确不想让 pi 碰其他 harness 的配置时才选 D。
    - 选 A 的写入见 3.13。选 B/C 的不写 mcp.json，由用户交互执行。
    - **提醒**：导入的 server 能否真正连上，取决于其启动命令在 PATH 中（如 `npx` 需 Node、`uvx` 需 `uv`、自定义 CLI 需自行安装）。pi 会尝试拉起，拉不起的会在 `/mcp` 里显示失败状态。

> 访谈完成后，**先向用户复述一遍汇总的答案**（含 skills 源选择 + MCP 接入方式），确认无误再进入阶段 2。

---

## 阶段 2：安装外部依赖（按访谈结果执行，跳过不用的）

### 2.1 GitHub CLI（仅当用户要用 gh）
- Windows：`winget install --id GitHub.cli -e`
- macOS：`brew install gh`
- Linux：见 https://github.com/cli/cli#installation
- 装完重开终端，执行 `gh auth login`，按交互提示用浏览器或 token 登录。
- 验证：`gh auth status`

### 2.2 LSP server（仅当用户写对应语言且装了 pi-lsp）
- TS/JS：`npm i -g typescript-language-server typescript`
- Rust：`rustup component add rust-analyzer`（需先装 rustup）

### 2.3 VS Code（仅当用户要用外部编辑器）
- Windows：`winget install Microsoft.VisualStudioCode`
- macOS：`brew install --cask visual-studio-code`
- 验证：`code --version`

---

## 阶段 3：写入配置文件

所有路径前缀：
- Windows：`C:/Users/<USER>/.pi/...`
- macOS/Linux：`/Users/<USER>/.pi/...` 或 `/home/<USER>/.pi/...`
- 用 `$HOME` 探测得到的 `HOME` 替换下面的 `<HOME>`。

> 配置文件里**优先用 `~`** 表示主目录（pi 能跨平台展开），避免硬编码用户名。只有 `clonePath`、`shellPath`、`external_directory` 这种必须是绝对路径的，才用访谈得到的值。

---

### 3.1 `settings.json` → `<HOME>/.pi/agent/settings.json`

```json
{
  "lastChangelogVersion": "<按当前 pi 版本>",
  "theme": "dark",
  "defaultProvider": "<A1>",
  "defaultModel": "<A1>",
  "shellPath": "<B4 仅 Windows 写；mac/linux 删此行>",
  "externalEditor": "<C5 用 vscode 则写 'code --wait'；否则删此行>",
  "showCacheMissNotices": true,
  "collapseChangelog": true,
  "enableInstallTelemetry": false,
  "enableAnalytics": false,
  "defaultThinkingLevel": "high",
  "compaction": {
    "enabled": true,
    "reserveTokens": 16384,
    "keepRecentTokens": 20000
  },
  "retry": {
    "enabled": true,
    "maxRetries": 3,
    "baseDelayMs": 2000,
    "provider": { "maxRetries": 0, "maxRetryDelayMs": 60000 }
  },
  "steeringMode": "one-at-a-time",
  "followUpMode": "one-at-a-time",
  "images": { "autoResize": true },
  "markdown": { "mermaid": "final" },
  "enableSkillCommands": true,
  "skills": [
    <I15: 用户勾选的 skills 源路径列表，每项为字符串，如 "~/.claude/skills"、"~/.codex/skills"；没选任何源则删掉整个 skills 字段>
  ],
  "packages": [
    "npm:@gotgenes/pi-permission-system@25.0.0",
    "npm:@gotgenes/pi-subagents@19.2.2",
    "npm:@gotgenes/pi-subagents-worktrees@0.3.0",
    "npm:@juicesharp/rpiv-ask-user-question@2.4.0",
    "npm:@juicesharp/rpiv-i18n@2.4.0",
    "npm:@juicesharp/rpiv-todo@2.4.0",
    "npm:@narumitw/pi-github-pr@0.49.3",
    "npm:@narumitw/pi-goal@0.51.0",
    "npm:@narumitw/pi-lsp@0.49.4",
    "npm:@narumitw/pi-plan-mode@0.49.3",
    "npm:@narumitw/pi-statusline@0.49.6",
    "npm:@narumitw/pi-worktree@0.50.0",
    "npm:pi-background-tasks@2.3.0",
    "npm:pi-hermes-memory@0.9.4",
    "npm:pi-mcp-adapter@2.23.0",
    "npm:pi-web-access@0.22.0"
  ]
}
```

**packages 取舍规则**：
- **命令放行插件（J23）**：A → 保留 `"npm:@gotgenes/pi-permission-system@25.0.0"`；B → 删该行、加 `"npm:@ogulcancelik/pi-auto-permissions"`；C → 删该行且不加替代。A 与 B 严格互斥，不能共存。
- **状态栏模式（J16）**：基础 → 保留 `"npm:@narumitw/pi-statusline@0.49.6"`；高级 → 删该行、加 `"npm:@narumitw/pi-starship"`；不装 → 删该行且不加替代。基础与高级不能共存。
- 用户不要语音 → 不变（rpiv-voice 本就不在清单里，默认不装）
- 用户用 rtk → 追加 `"npm:pi-rtk-optimizer@0.9.0"`；用户要语音 → 追加 `"npm:@juicesharp/rpiv-voice@2.4.0"`
- 用户不写任何 LSP 语言 → 从清单删 `"npm:@narumitw/pi-lsp@0.49.4"`
- 用户不用 GitHub → 可删 `"npm:@narumitw/pi-github-pr@0.49.3"`（可选）

**skills 取舍规则**：
- `enableSkillCommands: true` 固定写（启用 `/skill:name` 斜杠命令）。
- `skills` 数组每一项是**目录路径字符串**（`~` 开头或绝对路径），不是文件。
- 仅写阶段 0 探测存在且用户勾选的源；用户一个都没选 → 删掉整个 `skills` 字段（pi 仍会加载 `~/.pi/agent/skills` 与扩展自带的 skills）。
- 勾选的源目录里只要有 `SKILL.md` 的子目录就会被递归发现；无需手动列出每个 skill。

---

### 3.2 `models.json` → `<HOME>/.pi/agent/models.json`（provider/model 注册表 + 费用费率）

> settings.json 的 `defaultProvider`/`defaultModel` 只是指向“用哪个”；**provider 怎么连、模型有哪些字段、每百万 token 多少钱，全在 models.json**。这个文件不写，`/provider` 命令也配不了自定义 provider 的费率和兼容性。

**结构**：
```json
{
  "providers": {
    "<provider名>": {
      "name": "<显示名>",
      "baseUrl": "<API base URL>",
      "api": "openai-completions",
      "apiKey": "<明文 key 或 \"{env:VAR_NAME}\">",
      "authHeader": true,
      "headers": { "<自定义头>": "<值>" },
      "compat": { "supportsDeveloperRole": false, "thinkingFormat": "deepseek" },
      "models": [
        {
          "id": "<传给 API 的 model id>",
          "name": "<显示名>",
          "reasoning": true,
          "input": ["text"],
          "contextWindow": 1048576,
          "maxTokens": 393216,
          "thinkingLevelMap": { "minimal": null, "low": null, "medium": null, "high": "high", "max": "max" },
          "cost": { "input": 1.32, "output": 3.96, "cacheRead": 0.044, "cacheWrite": 1.32 }
        }
      ]
    }
  }
}
```

**字段说明**：
- `api`：`openai-completions` / `openai-responses` / `azure-openai-responses` / `anthropic` 等，取决于 provider 兼容哪种。
- `apiKey`：可明文，也可 `"{env:VAR_NAME}"` 引用环境变量（**推荐**，避免 key 进 git）。
- `compat`：`supportsDeveloperRole`、`thinkingFormat`（`deepseek`/`qwen`）等兼容开关。
- `thinkingLevelMap`：把 pi 的思考档映射到 provider 的值；某档设 `null` 表示“接受但透传空”。
- **`cost`**：**美元 / 每百万 token** 费率。`input`=未命中缓存的输入、`output`=输出、`cacheRead`=缓存命中读取、`cacheWrite`=缓存写入。**省略则默认全零**。

**`cost` 机制（务必读，否则会困惑“为什么费用是 0”）**：
- pi 在**每条 assistant 消息生成完**时，用**当时** model 的 `cost` 费率 × `usage` token 数算出费用（`calculateCost(model, usage)`），**固化写进 session JSONL**。之后 footer 的 `$cost` 只是累加这些已存储值。
- 因此：**models.json 加了 cost 之前的旧消息，cost 永远是 0**，不会回溯重算。`/reload` + 发新消息才开始按新费率累计；想要“从第一句就准”得开新 session。
- 不填 `cost` → 所有消息 cost 全零 → footer 的 `$cost` 恒为 `$0.000`（哪怕 token 用量正常）。

**定价来源（访谈 A1b 决定是否查）**：
- 若目标设备**已有 models.json 且里面已有 provider+model**：问用户“是否要我联网查各模型官方最新定价并更新 `cost` 字段？”。
  - 是 → AI 用 `web_search` 查厂商官方定价页（DeepSeek/GLM/Qwen/OpenAI/Anthropic/Google/xAI/MiniMax 等），取美元/百万 token 单价填入 `cost`。
  - 否 → 保留现有 `cost`（可能为空/全零，费用栏恒为 $0）。
- 若**没有 models.json**：按 A1 给的 provider+model 新建，`cost` 留空（用户事后可再让 AI 查价补）。

**取舍规则**：
- 保留用户既有 models.json 里的 provider/model/key，只按访谈增删或补 `cost`。
- 多 provider 各自独立块；同一 model id 在不同 provider 下分别定义。
- `apiKey` 强烈建议用 `"{env:VAR_NAME}"`，把 key 放环境变量，models.json 才能安全进 git。

---

### 3.3 `web-search.json` → `<HOME>/.pi/web-search.json`（注意在 `.pi/` 下，不在 `.pi/agent/`）

```json
{
  "searchRouting": {
    "providers": "<D8: ['exa','duckduckgo'] 或 ['duckduckgo']>",
    "fallbackOn": ["transient", "quota", "network", "invalid-response"]
  },
  "fetchRouting": {
    "providers": ["http", "jina"],
    "allowRemoteHostedProviders": false
  },
  "tools": {
    "webSearch": { "enabled": true },
    "sourceCheck": { "enabled": true },
    "fetchContent": { "enabled": true },
    "getSearchContent": { "enabled": true }
  },
  "commands": {
    "websearch": { "enabled": true },
    "curator": { "enabled": true },
    "search": { "enabled": true },
    "google-account": { "enabled": false }
  },
  "image": { "enabled": true },
  "allowBrowserCookies": false,
  "summaryGenerationDeadlineMs": 30000,
  "maxInlineContentChars": 24000,
  "workflow": "summary-review",
  "curatorTimeoutSeconds": 30,
  "autoOpenBrowser": <E9: true 或 false>,
  "githubClone": {
    "enabled": true,
    "maxRepoSizeMB": 350,
    "cloneTimeoutSeconds": 45,
    "clonePath": "<B2: 用户指定的绝对路径>"
  },
  "youtube": { "enabled": true },
  "video": { "enabled": true, "maxSizeMB": 50 },
  "pdf": { "enabled": true, "maxSizeMB": 20, "provider": "auto" },
  "ssrf": { "trustEnvProxy": <C7: true 或 false> }
}
```

---

### 3.4 状态栏配置 → `<HOME>/.pi/agent/` 下（按 J16 模式分支）

> J16 选「基础模式」写 `pi-statusline.json`；选「高级模式」写 `pi-starship.toml`；选「不装」跳过本节、不写任何文件。两者只能存在其一。

#### 3.4a 基础模式：`pi-statusline.json`（按 J16–J22 定制）

**全开示例**（供向用户展示用）：
```
░▒▓ 🤖 <模型名> • 🧠 <思考档> • 📁 <当前目录> • 🌿 <git分支> • ctx <上下文%>/<总窗口> • 📦 <保留缓存> CH<命中率%> • 💸 <花费>
```

```json
{
  "palettePreset": "<J17: ocean/dark/light/solarized>",
  "density": "<J18: compact/normal/comfortable>",
  "separator": "<J19: dot/bar/none>",
  "segments": <J16: 用户勾选的段数组，从 ["model","thinking","cwd","branch","context","cache","cost"] 中取子集>,
  "segmentText": {
    "model": {
      "truncationLength": <J20: 默认 40；false 不截断则删整段 model>,
      "truncationSymbol": "…",
      "truncationDirection": "<J20: middle/end>"
    },
    "context": {
      "prefix": "<J21: 默认 'ctx '>",
      "suffix": "<J21: 默认 ''>"
    }
  },
  "extensionStatusIcons": <J22: 默认 {"goal":"◎","mcp:*":"◈"}；用户自定义或删整段>
}
```

**取舍规则**：
- `segments` 只写用户在 J16 勾选的段，顺序按 `model→thinking→cwd→branch→context→cache→cost`。
- J20 选“不截断” → 删掉 `segmentText.model` 整段。
- J22 选“删掉” → 不写 `extensionStatusIcons` 字段（用扩展默认）。

#### 3.4b 高级模式：`pi-starship.toml`（按 J16 高级模板流程）

把用户在 J16 写的 `format` 模板 + `[模块]` 表原样写入 `<HOME>/.pi/agent/pi-starship.toml`。AI 补齐规则见 J16「AI 生成规则」。最小可用示例（即用户只给 `format` 一行时的默认落盘）：

```toml
format = """
$brand$model$thinking$directory$git_branch$git_status$activity$context$time"""
```

- 用户模板已含 `[model]`/`[cache]`/`[context.display]` 等表 → 原样保留，不覆盖。
- `cache` 若出现在 `format` 里 → 必须有 `[cache]\ndisabled = false`（默认禁用）。
- `cost` 若要永远显示（含 $0）→ `[[cost.display]]` 的 threshold=0 项 `hidden = false`。
- 写完用 `smol-toml` 或 `/starship status` 校验；无效字段会被警告并忽略，不会崩溃。

---

### 3.5 `pi-plan-mode.json` → `<HOME>/.pi/agent/pi-plan-mode.json`

```json
{
  "thinkingLevel": "high",
  "defaultPlanTools": ["read", "bash", "grep", "find", "ls"],
  "implementationPlanRetention": "clear-on-start",
  "defaultPlanExportPath": "PLAN.md",
  "safeSubcommands": {
    "git": ["status", "log", "diff", "show", "branch", "remote", "ls-files", "grep", "rev-parse", "blame", "describe", "merge-base", "ls-tree", "cat-file"],
    "gh": ["pr view", "pr list", "issue view", "issue list"]
  }
}
```

**取舍**：用户不用 gh（C6=否）→ 删掉整个 `"gh": [...]` 行。

---

### 3.6 `pi-goal.json` → `<HOME>/.pi/agent/pi-goal.json`

```json
{
  "toolVisibility": "after-first-goal",
  "experimental": { "goals": false },
  "rpc": { "enabled": false },
  "continuationLimits": {
    "automaticTurns": <H14: 默认 20>,
    "noProgressTurns": <H14: 默认 5>
  }
}
```

---

### 3.7 `subagents.json` → `<HOME>/.pi/agent/subagents.json`

```json
{
  "maxConcurrent": <H13: 默认 4>,
  "defaultMaxTurns": 12,
  "graceTurns": 3,
  "consumedSessionRetentionMinutes": 10,
  "unconsumedSessionRetentionMinutes": 120,
  "abortAllOnInterrupt": false
}
```

---

### 3.8 `hermes-memory-config.json` → `<HOME>/.pi/agent/hermes-memory-config.json`（原样，`~` 跨平台）

```json
{
  "memoryMode": "policy-only",
  "memoryPolicyStyle": "compact",
  "memoryCharLimit": 5000,
  "userCharLimit": 5000,
  "projectCharLimit": 5000,
  "memoryDir": "~/.pi/agent/pi-hermes-memory",
  "projectsMemoryDir": "projects-memory",
  "sessionSearch": { "variant": "anchors" },
  "nudgeInterval": 10,
  "nudgeToolCalls": 15,
  "reviewRecentMessages": 20,
  "reviewEnabled": false,
  "reviewTransport": "direct",
  "memoryOverflowStrategy": "auto-consolidate",
  "autoConsolidate": true,
  "correctionDetection": false,
  "failureInjectionEnabled": false,
  "consolidationTimeoutMs": 180000,
  "flushOnCompact": true,
  "flushOnShutdown": true,
  "flushMinTurns": 6,
  "flushRecentMessages": 20,
  "standingInstructionsEnabled": true
}
```

---

### 3.9 `pi-lsp.json` → `<HOME>/.pi/agent/pi-lsp.json`（按 G12 选语言）

**只写用户要的语言对应的 server 段**：

```json
{
  "timeout": 30000,
  "servers": {
    "typescript": {
      "command": ["typescript-language-server", "--stdio"],
      "extensions": [".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"],
      "skipDirectories": ["node_modules", ".next", "out", "coverage", "target"]
    },
    "rust-analyzer": {
      "command": ["rust-analyzer"],
      "extensions": [".rs"],
      "pullDiagnosticsGraceMs": 5000,
      "skipDirectories": ["target"]
    }
  }
}
```

- 只写 TS → 删 `rust-analyzer` 段
- 只写 Rust → 删 `typescript` 段
- 都不写 → 不创建此文件，并从 settings.json 的 packages 删 `@narumitw/pi-lsp`

---

### 3.10 命令放行配置 → 按 J23 分支

> J23=A 写 pi-permission-system 配置；J23=B 写 pi-auto-permissions 配置；J23=C 不写任何文件（pi 原生全放行，最不安全）。

#### 3.10a A：`pi-permission-system/config.json` → `<HOME>/.pi/agent/extensions/pi-permission-system/config.json`

**先建目录**：`mkdir -p <HOME>/.pi/agent/extensions/pi-permission-system`

下面是**基础模板（无 rtk、跨平台路径用 `~`）**。策略部分（敏感文件 deny、危险命令 deny、只读白名单）跨平台通用，直接照搬。

```json
{
  "$schema": "https://raw.githubusercontent.com/gotgenes/pi-packages/main/packages/pi-permission-system/schemas/permissions.schema.json",
  "debugLog": false,
  "permissionReviewLog": true,
  "yoloMode": <J23: true=自动放行 / false=保守模式，默认 true>,
  "doublePressToConfirm": true,
  "toolInputPreviewMaxLength": 400,
  "toolTextSummaryMaxLength": 120,
  "piInfrastructureReadPaths": [
    "~/.pi/agent/**"
  ],
  "permission": {
    "*": "allow",
    "path": {
      "*": "allow",
      "*.env": "deny",
      "*.env.*": "deny",
      "*.env.example": "allow",
      "*.env.*.example": "allow",
      "~/.ssh/*": "deny",
      "~/.aws/*": "deny",
      "~/.config/gcloud/*": "deny",
      "~/.kube/config": "deny",
      "**/*.pem": "deny",
      "**/*.key": "deny"
    },
    "read": "allow",
    "write": "allow",
    "edit": "allow",
    "grep": "allow",
    "find": "allow",
    "ls": "allow",
    "bash": {
      "*": "ask",
      "cat *": "allow",
      "head *": "allow",
      "tail *": "allow",
      "less *": "allow",
      "ls *": "allow",
      "tree *": "allow",
      "stat *": "allow",
      "file *": "allow",
      "wc *": "allow",
      "du *": "allow",
      "df *": "allow",
      "grep *": "allow",
      "rg *": "allow",
      "find *": "allow",
      "fd *": "allow",
      "diff *": "allow",
      "cmp *": "allow",
      "comm *": "allow",
      "shasum *": "allow",
      "cksum *": "allow",
      "pwd": "allow",
      "whoami": "allow",
      "id": "allow",
      "hostname": "allow",
      "uname *": "allow",
      "date": "allow",
      "uptime": "allow",
      "ps *": "allow",
      "which *": "allow",
      "type *": "allow",
      "git status": "allow",
      "git status *": "allow",
      "git diff *": "allow",
      "git log *": "allow",
      "git show *": "allow",
      "git blame *": "allow",
      "git ls-files *": "allow",
      "git branch": "allow",
      "git branch --show-current": "allow",
      "git remote -v": "allow",
      "pnpm test*": "allow",
      "pnpm typecheck *": "allow",
      "pnpm lint *": "allow",
      "pnpm format:check *": "allow",
      "cargo test *": "allow",
      "cargo check *": "allow",
      "cargo fmt --all --check": "allow",
      "sudo *": {
        "action": "deny",
        "reason": "Run privileged commands manually after reviewing them."
      },
      "rm -rf *": {
        "action": "deny",
        "reason": "Recursive forced deletion is disabled; use a recoverable or narrowly scoped operation."
      },
      "git reset --hard *": "deny",
      "git clean *": "deny",
      "git push --force*": "deny",
      "npm publish *": "deny",
      "pnpm publish *": "deny",
      "cargo publish *": "deny"
    },
    "mcp": "allow",
    "skill": "allow",
    "external_directory": {
      "*": "ask",
      "~/.pi/agent/*": "allow",
      "<B3: npm 全局 node_modules 绝对路径>/**": "allow"
    }
  }
}
```

**取舍规则**：
- 用户用 rtk（F11=是）→ 在 bash 段补回所有 `rtk *` 镜像条目（见附录 A）
- 用户不写 Rust（G12 不含 Rust）→ 删 `cargo test *`、`cargo check *`、`cargo fmt --all --check` 三条
- `external_directory` 的 npm 路径用阶段 0 探测的 `npm root -g` 结果（绝对路径），让用户确认
- `piInfrastructureReadPaths` 用 `~/.pi/agent/**` 跨平台，无需改
- J23 选 A 且 yoloMode 关 → 把 `yoloMode` 设 `false`；开 → `true`（默认）

#### 3.10b B：`pi-auto-permissions/config.json` → `<HOME>/.pi/agent/pi-auto-permissions/config.json`

**先建目录**：`mkdir -p <HOME>/.pi/agent/pi-auto-permissions`

```json
{
  "rules": [
    { "pattern": "\\bgit\\s+commit\\b", "flags": "i", "level": "guarded", "group": "git", "label": "Git commit" },
    { "pattern": "\\bgit\\s+push\\b", "flags": "i", "level": "guarded", "group": "git", "label": "Git push" },
    { "pattern": "\\bnpm\\s+publish\\b|\\bpnpm\\s+publish\\b|\\bcargo\\s+publish\\b", "flags": "i", "level": "convention", "group": "publish", "label": "Publish", "message": "Use the configured release workflow." }
  ],
  "reviewer": {
    "provider": "<J23b: 你的 provider，如 cannbot-dashscope>",
    "model": "<J23b: 低价 model，如 glm-5.2>",
    "reasoningEffort": "low",
    "timeoutMs": 30000
  }
}
```

- `level: guarded` → 守护模型审；`level: convention` → 直接拦（配 `message` 反馈）
- `pattern` 是 JS 正则；匹配的命令才审，不匹配的直接放行
- 失败即拦（模型缺失/超时/无法解析 → 不自动放行）
- **与 pi-permission-system 严格互斥**，二者都装会双重 gate bash

#### 3.10c C：不装（无配置文件）

J23=C 时不写任何权限配置文件，packages 也不加 permission 扩展。pi 用原生行为：所有 bash/文件操作直接执行，无确认、无 deny、无 yolo。仅适合完全可信的隔离环境。

---

### 3.11 `fusion-models.json` —— **默认不创建**

仅在用户明确要"模型融合"（多候选并行+评分合并）且能提供 ≥2 个不同 model id 时才创建。默认跳过。

### 3.12 后台任务更新检查（环境变量，仅当 J24=关时设置）

pi-background-tasks 的 footer 更新提示（`🔌 bg ⬆ vX /bg-update`）由环境变量控制，不在 JSON 配置里。

仅当第 5 轮 J24 选“关”时，往用户的 shell 启动文件写：
```sh
export PI_BG_DISABLE_UPDATE_CHECK=1
# 或 PI_OFFLINE=1（会连带关闭更多联网检查）
```
- Windows Git Bash → `~/.bashrc` 或 `~/.bash_profile`
- macOS/Linux → `~/.zshrc` / `~/.bashrc`
- 或在系统环境变量里加 `PI_BG_DISABLE_UPDATE_CHECK=1`

J24=开（默认）则什么都不做。

### 3.13 `mcp.json` → `<HOME>/.pi/agent/mcp.json`（仅当第 6 轮 K25 选 A 时创建）

pi-mcp-adapter 默认不从其他 harness 读 MCP 配置（`hostConfigDiscovery: "off"`）。选 A 才开启自动导入。

```json
{
  "settings": {
    "hostConfigDiscovery": "on"
  }
}
```

**效果**：pi 启动时自动从下列路径读取并合并 MCP server（只读，不改外部文件，最低优先级）：
- `~/.claude.json`、`~/.claude/mcp.json`、`~/.claude/claude_desktop_config.json`（Claude Code）
- `~/.codex/config.toml`、`~/.codex/config.json`（Codex）
- `~/.cursor/mcp.json`、`~/.windsurf/mcp.json`、`./.vscode/mcp.json`、`~/.config/opencode/opencode.json`
- 通用标准：`~/.config/mcp/mcp.json`、`~/.agents/mcp.json`

**取舍**：
- K25=A → 写此文件。
- K25=B 或 C → 不写此文件，由用户在 pi 里跑 `/mcp setup` 或 `pi-mcp-adapter init --discover-host-configs` 手动导入。
- K25=D → 不写此文件，保持 `off`。
- 若 pi 自己的 mcp.json 里有同名 server，pi 自己的优先（导入是最低优先级 fallback）。
- 导入的 server 能否连上取决于启动命令在 PATH（`npx`/`uvx`/自定义 CLI）；连不上的在 `/mcp` 里显示失败，不影响其他 server。

---

## 阶段 4：验证

1. **JSON 合法性**：对每个写好的 `.json` 跑 `python -m json.tool < file > /dev/null`，全 OK。
2. **文件清单**：`find <HOME>/.pi -type f -name "*.json" | grep -v sessions | grep -v node_modules`，对照阶段 3 应有：
   - `.pi/agent/settings.json`
   - `.pi/agent/models.json`（若写了 provider/费率）
   - `.pi/web-search.json`
   - `.pi/agent/pi-statusline.json`（基础模式）或 `.pi/agent/pi-starship.toml`（高级模式）
   - `.pi/agent/pi-plan-mode.json`
   - `.pi/agent/pi-goal.json`
   - `.pi/agent/subagents.json`
   - `.pi/agent/hermes-memory-config.json`
   - `.pi/agent/pi-lsp.json`（若启用）
   - `.pi/agent/extensions/pi-permission-system/config.json`（J23=A）或 `.pi/agent/pi-auto-permissions/config.json`（J23=B）
3. **重启 pi**：让 pi 读取 `settings.json` 的 `packages` 自动 `npm install` 全部扩展。
4. **装后验证**：
   - `gh auth status`（若用 gh）
   - `typescript-language-server --version` / `rust-analyzer --version`（若用对应 LSP）
   - pi 启动后状态栏应显示配置的段：基础模式见 J16 勾选段（默认 ocean 配色）；高级模式见 `pi-starship.toml` 的 `format` 拼出的样子
5. **provider 凭证**：用 pi 的 `/provider` 命令配置访谈 A1 的 provider + API key（或写入 `auth.json`）。

---

## 附录 A：rtk 工具链条目（仅当用户用 rtk 时追加到 permission.bash）

```
"rtk read *": "allow",
"rtk grep *": "allow",
"rtk find *": "allow",
"rtk ls *": "allow",
"rtk git status *": "allow",
"rtk git diff *": "allow",
"rtk git log *": "allow",
"rtk git show *": "allow",
"rtk git branch --show-current": "allow",
"rtk pnpm test*": "allow",
"rtk pnpm typecheck *": "allow",
"rtk pnpm lint *": "allow",
"rtk pnpm format:check *": "allow",
"rtk cargo test *": "allow",
"rtk cargo check *": "allow",
"rtk cargo fmt --all --check": "allow",
"rtk sudo *": "deny",
"rtk rm -rf *": "deny",
"rtk git reset --hard *": "deny",
"rtk git clean *": "deny",
"rtk git push --force*": "deny",
"rtk npm publish *": "deny",
"rtk pnpm publish *": "deny",
"rtk cargo publish *": "deny"
```

---

## 附录 B：访谈答案记录表（执行时在会话内存中跟踪，不落盘）

| 编号 | 问题 | 用户答案 |
|---|---|---|
| A1 | provider + model | |
| A1b | 是否查官方定价更新 cost（仅已有 models.json 时问） | |
| B2 | github clone 缓存目录 | |
| B3 | npm 全局 node_modules 路径 | |
| B4 | shellPath（仅 Windows） | |
| C5 | 用 VS Code？ | |
| C6 | 装/用 gh？ | |
| C7 | 走代理？ | |
| D8 | 有 Exa key？ | |
| E9 | autoOpenBrowser？ | |
| F10 | 要语音？ | |
| F11 | 用 rtk？ | |
| G12 | 写哪些语言（TS/Rust） | |
| H13 | maxConcurrent | |
| H14 | continuationLimits | |
| I15 | skills 来源（勾选 .claude/.codex/.agents/.cursor/.pi 等） | |
| J16 | 状态栏模式（基础/高级/不装）+ 基础模式勾选段/高级模式模板 | |
| J17 | 配色板 palettePreset | |
| J18 | 密度 density | |
| J19 | 分隔符 separator | |
| J20 | 模型名截断（开/关+长度+方向） | |
| J21 | 上下文段 prefix/suffix | |
| J22 | extensionStatusIcons 图标 | |
| J23 | 命令放行插件（A pi-permission-system / B pi-auto-permissions / C 不装） | |
| J23b | A: yoloMode 开/关；B: reviewer provider/model + guarded/convention 规则；C: 无 | |
| J24 | 后台任务更新检查（开/关） | |
| K25 | MCP 接入方式（A 自动 / B 手动 / C CLI / D 不复用） | |

---

## 执行原则（给 pi 的提示）

1. **先访谈、后动手**：阶段 1 全部问完并复述确认，再进阶段 2/3。
2. **路径绝不硬编码**：阶段 0 探测 + 阶段 1 确认，能 `~` 就 `~`，必须绝对路径的才用用户指定值。
3. **每写完一个文件立即校验 JSON**。
4. **保留用户既有配置**：若目标设备已有 settings.json 中的 provider/model/shell 等，保留这些值，只合并本指南的行为参数与 packages。
5. **取舍清晰**：packages、pi-lsp、pi-plan-mode 的 gh 段、permission 的 rtk/cargo 条目，严格按访谈结果增删。
6. **最后向用户报告**：列出实际写入的文件清单、跳过的项、需要用户手动完成的剩余步骤（如 `gh auth login`、`/provider` 配 key）。
