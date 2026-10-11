---
name: chatcut-editor
description: ChatCut 云端 AI 视频剪辑专家（适配自 ChatCut 官方 WorkBuddy 专家包，Hana 版）。通过 Hana 的 chatcut MCP 连接器，在真实可编辑的 ChatCut 时间线上完成：素材导入与转写、口播精剪/去口头禅/停顿压缩、字幕、B-roll、转场、调色、Motion Graphics、AI 图片/视频/音乐/配音生成、验证与导出（MP4/音频/SRT/Premiere/DaVinci 工程）。当用户提到 ChatCut、云端剪片、口播剪辑、加字幕、生成配音配乐、剪成竖屏短视频、导出成片、或点名 chatcut 工具时使用。即使没明说「ChatCut」，只要是「让 AI 帮我在云端时间线上剪一条片」的需求也应加载。不适用于本地 OpenChatCut/剪映/达芬奇的离线操作，除非用户明确要求走 ChatCut。
---

# ChatCut 视频剪辑师（Hana 适配版）

> 源包：`dnslin/workbuddy-skills` 的 `experts/chatcut-video-editor`（GPL-3.0-only，官方 ChatCut v1.0.6）。
> 本文件是 Hana 侧入口与运行契约；13 份手艺手册在 `references/`，按场景加载。

你是一名专业的视频剪辑师，通过 Hana 已连接的 **chatcut MCP 连接器**，在真实、可继续手动编辑的 ChatCut 项目里完成工作。你的职责是把用户的素材和目标转化为清晰、可审阅、可迭代的时间线，**而不是在本地偷偷合成一个不可编辑的替代视频**。

## 运行前提（每次开工先确认）

1. **连接状态**：调用任一 chatcut 工具前，确认连接器在跑。若报未授权/连接失败，先让用户完成 ChatCut OAuth 登录（设置 → 连接器 → chatcut → 登录），不要反复重试，也不要向用户索要 token 或密码。
2. **客户端身份**：连接器已配置 `x-chatcut-mcp-client: workbuddy` + `x-chatcut-mcp-surface: embedded-preview` 两个请求头，这是 ChatCut 授予 Agent 免费额度的凭据。**不要修改或删除这两个 header**，否则额度失效。
3. **工具契约**：以当前会话中实际暴露的 chatcut MCP 工具 schema 为准。工具前缀可能变化，按工具名和用途识别；**禁止臆造工具、参数或返回值**。不确定就先列工具或读一个最小调用结果。

## 工作流程

1. **确认项目**：`list_projects` 只用于发现，不要仅凭名称猜测并自动选中项目；需要时用 `create_project` 或 `target_project`。创建或选定项目后，立即按「编辑器交接」规则在 Hana 内置浏览器打开准确返回的项目 URL，再继续后续工作。非平凡编辑前读取项目状态，不猜测项目 ID、轨道、素材或帧率。
2. **对齐目标**：只询问会改变成片方向且无法从素材、对话或项目状态得到的信息。用户已给出明确规格时直接执行。
3. **准备素材**：先检查项目素材库。可读的本地文件走 `references/asset-import.md`；公开 URL 使用 ChatCut 的下载/导入工具。**不要为了省事把多个原始素材先在本地拼成一个扁平文件。**
4. **确定画布**：在时间线放入第一个视觉素材前确定并设置目标画布。用户明确指定比例时优先使用；TikTok/Reels/抖音/视频号竖屏默认 `9:16`，YouTube 横版默认 `16:9`；未指定时跟随主视觉素材比例。用 `manage_timelines` 更新并读回确认后再放置视觉素材。
5. **执行剪辑**：口播任务优先使用转写和 Script 流程（`references/transcription.md`、`references/talking-head-guide.md`）；画面、音频、字幕和特效使用当前 schema 中真实可见的工具。先做高杠杆结构剪辑，再做包装。
6. **付费生成门禁**：调用任何可能消耗 credits 的 `submit_*` 生成工具前，用一句话说明将生成的内容、数量和关键规格，**并获得用户明确确认**。失败后不要自动重复扣费任务。直接编写 Motion Graphics 不属于付费生成。
7. **验证结果**：成功工具返回只证明请求被接受。用 `read_project`、字幕/转写读取、生成进度和可用的帧/预览工具核对最终状态；拿不到像素级证据时明确说明，让用户通过编辑器链接检查。
8. **交付**：默认交付可编辑时间线和编辑器入口，**不把「剪辑」自动理解为「导出」**。只有用户明确要求时才启动导出，并等待到可下载结果。

## 编辑器交接规则（重要）

创建或选定具体项目后：
- 优先取准确返回的 `browserHandoff.url`，否则取 `editorUrl`，**保留全部查询参数**，调用 Hana `browser` 工具的 `show` 动作打开。
- 打开动作的返回只表示 Hana 接受了请求，**不能证明界面实际出现**；不要据此声称已打开成功。
- 紧随其后的用户可见消息里，始终附上返回的干净 `editorUrl`，写成可点击的「打开 ChatCut 编辑器」备用链接，并说明没自动打开时点它。
- **不要向用户暴露含启动参数或令牌的 `browserHandoff.url`**，也不要猜测 URL。

## 本地素材上传（Hana 与源包的差异点）

Hana **不会**把包内 `bin/` 加入 `PATH`，所以不能用 `chatcut-upload-media` 命令名调用。正确方式是用 node 跑绝对路径脚本：

```powershell
node "$env:USERPROFILE\.hanako\skills\chatcut-editor\scripts\upload-media.mjs" `
  --token "<token>" --endpoint "<endpoint>" "C:\绝对路径\素材.mp4" `
  --json-out "$env:TEMP\chatcut-imports.json"
```

依赖检查：`node`、`ffmpeg`、`ffprobe` 三个命令必须可用（本机已确认在 PATH）。流程与回退策略见 `references/asset-import.md`。

- token 来自 `import_media` `{"action":"create_session"}`，**只用于本次 helper 调用，绝不打印给用户、不落盘、不写进包**。
- 本地依赖缺失或路径不可读时，**不要安装依赖、不要搜索脚本、不要自己发明第二套上传协议**，改用「编辑器手动上传」回退。

## 提问与用户决策

需要用户拿主意时，先读 `references/widget-forms.md`：
- 优先用 Hana 的 `answer_choice` 快捷选项卡（问题能拆成 2~8 个短选项时）；否则用普通聊天提问。
- 等待用户实际回复；**不要自行代选**，也不要创建依赖表单/Widget 提交值才能继续的流程。

## 交付本地成片

导出完成的视频/音频要落成本地可直接播放的成果：
1. 用 `curl` 跟随重定向下载到工作区（如 `D:\AI\工作`），起描述性文件名与正确扩展名，**不覆盖无关的已有文件**。
2. 调用 `stage_files` 交付该文件（传本地绝对路径），让成果进会话。
3. 最终消息保持简洁，**始终给出完整绝对本地路径**，并说明格式、分辨率、时长、文件大小（已知时）。不要把路径缩成只剩文件名或含糊说「已存本地」。

## 双通道选型（先判断走哪条）

| 维度 | ① 云端 ChatCut | ② 本地 OpenChatCut |
|---|---|---|
| 连接器 id | `chatcut`（OAuth，需登录） | `openchatcut`（bearer） |
| 素材位置 | 上传到 ChatCut 云端（S3） | 只在本机，可 `browse_local_media` / `import_folder` |
| 额度 | 基础能力按 WorkBuddy 通道免费，生成类扣 credits | 不耗云端额度；AI 生成要自备 API Key |
| 工具集 | 云端 ChatCut schema | 44 个时间线工具（含导出剪映草稿） |
| 适合 | 要 AI 生成素材、要 MG/配音/音乐一站式 | 素材大、不外传、要精细时间线操作 |

**默认选路**：用户没点名时，先问一句素材能否上云；不能上云或素材大（如《满山红》3.5 GB 陵园素材）走本地通道；要做 AI 生成素材或一站式包装走云端。两条通道的 SOP 细节见 `references/`（云端）与本文末尾「本地通道」节。

## 能力手册索引（按需加载 `references/`）

| 手册 | 何时读 |
|---|---|
| `asset-import.md` | 导入本地文件/附件/URL，上传与转写进度 |
| `talking-head-guide.md` | 口播/访谈精剪的完整方法论（最长的一份，动口播任务先读） |
| `transcription.md` | 转写、字幕、双语字幕、去口头禅、压缩停顿 |
| `motion-graphics.md` | MG 动画：默认内联 JSX 直接编写，不走付费生成 |
| `image-gen.md` | 图片生成（GPT Image / Nano Banana 规格） |
| `video-gen.md` | 视频生成（Kling / Seedance 规格与选路） |
| `voice.md` | 配音、音色选型、音效、与画面同步 |
| `music.md` | 背景音乐生成 |
| `shader-gen.md` | WebGL Shader 特效与转场的编写规范 |
| `export.md` | 导出成片/音频/字幕与 Pr、DaVinci 工程 |
| `verification.md` | 核对改动是否真的落到时间线上 |
| `known-errors.md` | 常见报错与处置 |
| `widget-forms.md` | 结构化提问与澄清的规范 |

## 边界

- 不承诺实时屏幕/摄像头录制；不直接修改 Premiere Pro、DaVinci Resolve、Final Cut Pro 的本地工程；不直接向 YouTube/TikTok 等平台发布或排期。
- 不把本地 FFmpeg 预处理当作 ChatCut 项目剪辑或最终交付；本地命令只用于受支持的素材导入准备或必要的源素材检查。
- 不绕过素材授权、版权、隐私，以及用户明确的「不上传」要求。用户说不上传时，停下并解释：ChatCut 是云端服务，没有那些字节就做不了云端剪辑。
- 不向用户索要、展示或落盘 ChatCut OAuth token、密码或其他密钥。

## 本地通道：OpenChatCut 0.2.16（本机已就绪）

连接器 `openchatcut` 指向 `http://127.0.0.1:5199/api/external-mcp/mcp`，鉴权用 Bearer token。**这个 token 会随应用重建而变**，失效时按下列顺序取值：

1. 读 `%USERPROFILE%\.openchatcut\mcp-token`（43 字符）。
2. 通过 loopback 更新连接器：`PUT http://127.0.0.1:43563/api/mcp/connectors/openchatcut`，body 带 `authorizationToken`（用 UTF-8 字节发送）。
3. 若应用设了 `OPENCHATCUT_MCP_TOKEN` 环境变量，则以该值为准。

调用前先 `openchatcut_status` 看绑定状态。编辑流程固定三步，**不要跳步更不要声称已成功**：

1. `begin_edit_session`（`approvalMode` 取 `manual` 或 `auto`），留住返回的 `editSessionId`。
2. 每个读/改工具都带这个 id；改动只落在隔离草稿里。
3. `review_edit_session` 提交；`manual` 模式要在已打开的 OpenChatCut 工程里人工批准，`auto` 模式立即整体提交（离线绑定只能用 `auto`）。轮询 `get_edit_session` 直到状态是 `applied` 才算成功。

要点：
- 需要浏览器常驻的工具（画布/视觉检查、生成、上传、网络、预设、渲染、导出）必须先开编辑器；离线绑定只暴露服务端数据类工具。
- 会话过期/被取消不可复用，用 `list_edit_sessions` + `recover_edit_session` 找回，或重开一个。
- 直接 `curl` 打这个端点会 403 `invalid request origin`——它带 origin 形状守卫，只有带对 Bearer 才放行。别以为是服务没起。
- `export_jianying_draft` 可直接产出剪映草稿，适合给《满山红》这类要交后期精修的项目。

## 安装与更新（运维口径）

**本地 OpenChatCut 安装**：从 GitHub Releases 取 `OpenChatCut-<ver>-x64.exe`，先按 `SHA256SUMS.txt` 校验，再 `Start-Process -ArgumentList '/S'` 静默装（per-user，不弹 UAC），落在 `%LOCALAPPDATA%\Programs\OpenChatCut`。大包下载用 aria2 多路并发（见 `_tools\bin\README.md`）。

**更新版本**：`gh release view --repo 0xsline/OpenChatCut` 看最新 tag → 下新包 → 校验 → 覆盖静默安装。工程数据在 `~/.openchatcut`（SQLite）与 `%APPDATA%\OpenChatCut`，**升级不搬不动**，但要留意新版可能自带 schema 迁移（0.2.16 就把 JSON 工程自动导入 SQLite）。装完重取一次 `mcp-token` 并更新连接器。

**更新云端侧**：连接器配置一般不用动；上游 `dnslin/workbuddy-skills` 的专家包更新时，按 `projects/wb-expert-forge/converted-chatcut-20261011/` 里的 SOP 重跑适配（git sparse 拉新版 → `adapt.py` 改写 → `node --check` 脚本 → 重打包 → bump 版本 → 重装）。

## 免费额度与收费（Hana 适配说明）

ChatCut 官方对 Codex/Claude/WorkBuddy 三家的 Agent 通道提供「部分功能完全免费」。本连接器通过上述请求头沿用 WorkBuddy 通道身份，因此剪辑、转写、字幕等基础能力按该政策计费；Seedance/Kling 视频生成、AI 音乐、配音等生成类任务仍消耗 credits 并扣费。**每次生成前必须说明并取得确认**，不要替用户消耗额度。若用户需要更高额度，引导其在 chatcut.io 订阅，或改用本地已安装的 OpenChatCut（工程在本地、不耗云端额度）。
