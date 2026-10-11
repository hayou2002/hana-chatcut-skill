# hana-chatcut-skill

把 **ChatCut**（云端 AI 视频剪辑）和 **OpenChatCut**（开源本地版）接进 [Hana Agent](https://openhanako.com) 的 skill + MCP 连接器套件。

> 来源：由 `dnslin/workbuddy-skills` 的 `experts/chatcut-video-editor`（ChatCut 官方 WorkBuddy 专家包，v1.0.6）改写适配为 Hana 版本。改写产物 + 双通道接入 SOP + 复现脚本都在本仓。

![双通道架构](assets/ChatCut双通道架构.png)

## 它能给你什么

接好之后，你在 Hana 里一句话就能剪片：

- 导入本地素材/文件夹 → 转录 → 按文字稿删停顿、去口头禅 → 加字幕、B-roll、转场、调色
- 生成 AI 图片/视频/音乐/配音/MG 动画 → 验证 → 导出 MP4 / SRT / Premiere / DaVinci 工程
- 全程落在**真实可继续手动编辑的时间线**上，不是一次性生成的死视频

## 两条通道，按素材选

| | ① 本地 OpenChatCut | ② 云端 ChatCut |
|---|---|---|
| 素材去向 | 只在本机，不上传 | 上传到 ChatCut 云端（S3） |
| 额度 | 不耗云端额度；AI 生成需自备 Key | 基础能力可走 Agent 免费额度；生成类扣 credits |
| 工具 | 44 个时间线工具（含导出剪映草稿） | 云端 ChatCut 工具集 |
| 适合 | 素材大、涉密/不便外传、要精细时间线 | 要一站式 AI 生成、多端协作 |

**素材默认不外传**——大素材走本地通道；要 AI 生成素材或一站式包装才用云端。

## 快速开始（Hana 用户）

### 1. 装 skill

```powershell
# 下载本仓 dist/ 下的 skill-chatcut-editor-*.zip，或用 Hana 的扩展安装入口
```

然后让 Hana 执行：`extension_manager {kind:"skill", action:"install", source:{type:"local", path:"<zip>"}}`，**在应用里点确认**完成安装。另需 `node` / `ffmpeg` / `ffprobe` 在 PATH（本地素材上传要用）。

### 2. 接本地 OpenChatCut（推荐先接这条）

先装 [OpenChatCut](https://github.com/0xsline/OpenChatCut) 桌面版并打开一次，它会生成 `%USERPROFILE%\.openchatcut\mcp-token`。然后建连接器：

```powershell
$tok = (Get-Content "$env:USERPROFILE\.hanako\server-info.json" -Raw | ConvertFrom-Json).token
$mcp = (Get-Content "$env:USERPROFILE\.openchatcut\mcp-token" -Raw).Trim()
$body = @{ id='openchatcut'; name='OpenChatCut 本地剪辑'; transport='remote'
           url='http://127.0.0.1:5199/api/external-mcp/mcp'; authType='bearer'
           authorizationToken=$mcp; enabled=$true } | ConvertTo-Json -Compress
Invoke-WebRequest 'http://127.0.0.1:43563/api/mcp/connectors' -Method POST `
  -Headers @{ Authorization="Bearer $tok" } -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

验证：`mcp_connectors_status` 里 `openchatcut` 应为 `running`、`toolCount=44`。

> 注意：token 会随应用重建而变，失效时重取并 `PUT /api/mcp/connectors/openchatcut` 更新。

### 3. 接云端 ChatCut（可选）

```powershell
$body = @{ id='chatcut'; name='ChatCut 视频剪辑'; transport='remote'
           url='https://api.chatcut.io/api/external-mcp/mcp'; authType='oauth'; enabled=$true
           headers=@{ 'x-chatcut-mcp-client'='workbuddy'; 'x-chatcut-mcp-surface'='embedded-preview' }
         } | ConvertTo-Json -Compress -Depth 5
Invoke-WebRequest 'http://127.0.0.1:43563/api/mcp/connectors' -Method POST `
  -Headers @{ Authorization="Bearer $tok" } -Body ([Text.Encoding]::UTF8.GetBytes($body))
# 取授权链接，浏览器登录 ChatCut
$r = Invoke-RestMethod 'http://127.0.0.1:43563/api/mcp/connectors/chatcut/oauth/start' -Method POST `
      -Headers @{ Authorization="Bearer $tok"; 'Content-Type'='application/json' } -Body '{}'
$r.url
```

Hana 会自动完成 OAuth 的动态客户端注册（DCR）+ PKCE，无需手填 client_id。

> **关于那两个 header**：ChatCut 对 Codex / Claude / WorkBuddy 三家 Agent 通道提供「部分功能完全免费」，判定依据是请求头里的客户端标识（官方公开配置：Codex 用 `x-chatcut-mcp-surface: codex`，Kimi 用 `x-chatcut-mcp-client: kimi_work`）。这里沿用 WorkBuddy 的标识，以启用同一档免费额度。**这是借用第三方渠道身份，不是 ChatCut 给 Hana 的官方授权。**

## 仓库内容

```
chatcut-editor/            改写后的 Hana skill 源包（SKILL.md + 13 份手册 + 上传脚本）
dist/                      打包好的可安装 skill zip
adapt.py                   上游包 → Hana 的改写脚本（幂等，可重跑）
SOP-ChatCut接入与运维.md    完整接入/更新/排错/回滚 SOP
assets/                    架构图
LICENSE                    GPL-3.0（继承自上游声明）
```

**边界说明**：`chatcut-editor/` 这个 skill 本身只讲 ChatCut 剪辑能力，保持通用、不夹带任何具体的环境配置或运维事实；本文档（README）与 SOP 才承载接入步骤、连接器 id、路径等环境相关内容。这样 skill 被加载时不会引入无关上下文。

## 更新上游

```powershell
git clone --depth 1 --filter=blob:none --sparse https://github.com/dnslin/workbuddy-skills.git repo
cd repo; git sparse-checkout set experts/chatcut-video-editor
# 复制到本地 → python adapt.py（自检残留 0 处）→ node --check 脚本 → 重打包 → bump 版本
```

## 风险与免责

- **渠道身份伪装**：如上，走 WorkBuddy 通道拿免费额度属于借用他人渠道。ChatCut 若收紧校验（例如把身份绑定到签发令牌的宿主），该通道可能失效；由此产生的账号风险由使用者自负。
- **素材上云**：云端通道会把素材上传到 ChatCut 的 S3。涉密、未获授权、或用户明确要求不外传的素材，请走本地通道。
- **生成类扣费**：AI 图片/视频/音乐/配音等生成任务消耗 ChatCut credits，Hana 侧已设定「生成前必须说明并取得确认」的门槛，请勿绕过。
- **未签名程序**：OpenChatCut 的 Windows 安装包无代码签名，首次运行 SmartScreen 可能拦截；安装前请自行核对官方 SHA256。

## 许可与来源

- 上游：`dnslin/workbuddy-skills` → `experts/chatcut-video-editor`，其 `plugin.json` 声明 `license: GPL-3.0-only`（原包未附许可文件，本仓补齐 GPL-3.0 全文）。
- 本仓为上述内容的衍生适配版，按 GPL-3.0 分发。改编要点：把宿主机制从 WorkBuddy 换成 Hana（`present_files` → `browser` show / `stage_files`、`AskUserQuestion` → `answer_choice`、包内 `bin/` 入 PATH → 绝对路径调 `node`），并新增双通道连接器接入与运维 SOP。
- OpenChatCut 为独立开源项目（AGPL-3.0，`0xsline/OpenChatCut`），与本仓无隶属关系。
