# 一键配置 Pi

当你初次安装 [Pi](https://github.com/earendil-works/pi-coding-agent) 时，会发现缺少很多插件生态的支持，会特别难用，包括 Pi 自身的配置项。

## 使用方法

复制下面这段话发给 AI 即可，它会自动下载读取并按文档完成全部配置：

```
读取这篇文档，并按这篇文档内容进行配置
https://github.com/SeanDictionary/One-click-configuration-of-Pi/blob/main/pi%E9%85%8D%E7%BD%AE%E6%8C%87%E5%8D%97.md
```

安装内置 Skill 同理，复制下面这段话发给 AI 即可，它会读取 `SKILL.md` 并把 skill（`SKILL.md` + 同目录下的 `claude2pi.py`）下载安装到 `~/.pi/agent/skills/migrate-claude-session-to-pi/`：

```
安装这个 skill：读取它的 SKILL.md，并把 SKILL.md 与同目录下的 claude2pi.py 一起下载到 ~/.pi/agent/skills/migrate-claude-session-to-pi/，安装完成后简要告诉我它的用途与用法
https://github.com/SeanDictionary/One-click-configuration-of-Pi/blob/main/skills/migrate-claude-session-to-pi/SKILL.md
```

## 配置指南的作用

[pi 配置指南](pi配置指南.md) 会引导 AI 分阶段完成一次性的 pi 全套配置：先探测环境、再用结构化提问访谈你的偏好，然后按结果安装外部依赖、写入配置文件、最后验证。覆盖 Provider/模型、路径、外部工具、搜索引擎、抓取行为、扩展取舍、LSP 语言、并发续轮、Skills 来源、状态栏与权限模式、MCP 接入等。一份指南通吃 Windows / macOS / Linux，路径绝不硬编码，保留你既有配置。

## Skill 的作用

本仓库 `skills/` 目录下的每个子目录都是一个符合 [Agent Skills 标准](https://agentskills.io/specification) 的自包含 skill（含 `SKILL.md` + 脚本），交给 AI 按上文使用方法安装后即可自动发现并加载，也可用 `/skill:<名称>` 调用。

| Skill | 作用 |
|---|---|
| [`migrate-claude-session-to-pi`](skills/migrate-claude-session-to-pi) | 把 Claude Code 会话（`~/.claude/projects/.../*.jsonl`）转换成可被 `pi --resume` 打开的 pi 会话：早期历史浓缩为摘要、近期对话完整保留，工具调用映射到 pi 工具，thinking 省略、结果截断，provider/model 自动从 pi settings 读取。 |

## 许可

本指南与 skill 按 MIT 许可发布，可自由使用与修改。
