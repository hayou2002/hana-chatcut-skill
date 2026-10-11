"""把 WorkBuddy 版 ChatCut 专家包改写为 Hana 可用的 skill 手册。
只替换宿主机制措辞，保留全部 SOP 细节、工具名与参数。"""
import re, pathlib

SRC = pathlib.Path(r"C:\Users\Administrator\Desktop\OH-WorkSpace\_temp\chatcut-skill-20261011\repo\experts\chatcut-video-editor")
OUT = pathlib.Path(r"C:\Users\Administrator\Desktop\OH-WorkSpace\_temp\chatcut-skill-20261011\build\chatcut-editor")
REF = OUT / "references"
REF.mkdir(parents=True, exist_ok=True)

RULES = [
    # 1) 呈现文件 / 打开 URL
    (r"the “发送文件” tool", "Hana 的交付工具"),
    (r"WorkBuddy's `present_files`", "Hana 的 `browser` show / `stage_files`"),
    (r"call WorkBuddy's `present_files`", "调用 Hana 的 `browser` show（URL）或 `stage_files`（本地文件）"),
    (r"call `present_files`", "调用 `browser` show（URL）或 `stage_files`（本地文件）"),
    (r"`present_files\.previewed`", "`browser` show 的返回"),
    (r"`present_files`", "`browser` show / `stage_files`"),
    # 2) 提问机制
    (r"a host-native `AskUserQuestion` capability", "宿主原生的 `answer_choice` 快捷选项卡"),
    (r"host-native `AskUserQuestion` capability", "宿主原生的 `answer_choice` 快捷选项卡"),
    (r"宿主原生的 `AskUserQuestion`", "宿主原生的 `answer_choice` 快捷选项卡"),
    (r"`AskUserQuestion`", "`answer_choice`"),
    # 3) 工作目录
    (r"the current WorkBuddy task/workspace directory", "当前 Hana 工作区目录（如 D:\\AI\\工作）"),
    (r"absolute/workbuddy/task/", "absolute/hana/workspace/"),
    # 4) 本地上传命令：Hana 不把包 bin/ 加入 PATH
    (r"WorkBuddy adds the package `bin/` directory to `PATH`, so invoke the command by name from any working directory\.",
     "Hana 不会把包内 `bin/` 加入 `PATH`。必须用绝对路径直接调 node 运行本 skill 的 `scripts/upload-media.mjs`。"),
    (r"`chatcut-upload-media` is the only supported local upload command in this WorkBuddy expert",
     "`chatcut-upload-media` 是本专家在 Hana 中唯一受支持的本地上传方式"),
    (r"Run the package command directly\. On Windows PowerShell:",
     "在 Hana（Windows PowerShell）中直接运行："),
    (r"^(\s*)chatcut-upload-media --token",
     r'\1node "$env:USERPROFILE\\.hanako\\skills\\chatcut-editor\\scripts\\upload-media.mjs" --token'),
    # 5) 授权归属
    (r"OAuth、账号和连接由 WorkBuddy 的连接卡管理", "OAuth、账号和连接由 Hana 的 MCP 连接器（chatcut）管理"),
    (r"由 WorkBuddy 的连接卡管理", "由 Hana 的 MCP 连接器管理"),
    (r"the hosted WorkBuddy connector", "the Hana chatcut MCP connector"),
    # 6) 浏览器
    (r"在 WorkBuddy 内置浏览器中", "在 Hana 内置浏览器中"),
    # 7) 兜底
    (r"WorkBuddy", "Hana"),
]

def convert(text):
    for pat, rep in RULES:
        # rep 当作字面量处理，只保留 \1 这类组引用
        if rep.startswith(r"\1"):
            text = re.sub(pat, rep, text, flags=re.M)
        else:
            text = re.sub(pat, lambda m, r=rep: r, text, flags=re.M)
    return text

made = []
for skill_dir in sorted(p for p in (SRC / "skills").iterdir() if p.is_dir()):
    src_md = skill_dir / "SKILL.md"
    if not src_md.exists():
        continue
    body = convert(src_md.read_text(encoding="utf-8"))
    # 剥掉原 frontmatter（Hana 入口文件才需要 frontmatter，手册作为附件不需要）
    m = re.match(r"^---\n.*?\n---\n", body, re.S)
    if m:
        body = body[m.end():]
    parts = [body]
    for sub in sorted(list((skill_dir / "references").glob("*.md")) + list((skill_dir / "examples").glob("*.md"))):
        parts.append(f"\n\n---\n\n## 附：{sub.stem}\n\n" + convert(sub.read_text(encoding="utf-8")))
    out = REF / f"{skill_dir.name}.md"
    out.write_text("".join(parts), encoding="utf-8")
    resid = len(re.findall(r"WorkBuddy|workbuddy|present_files|AskUserQuestion", out.read_text(encoding="utf-8")))
    made.append((skill_dir.name, out.stat().st_size, resid))

for n, sz, r in made:
    print(f"{n:22} {sz:7} B  残留宿主字样={r}")
print(f"共 {len(made)} 份")
