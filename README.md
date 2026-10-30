# NovelAgent

一个在本地运行的 AI 互动文字游戏平台。你可以编写或导入世界书、设置玩家与关键 NPC，让故事随着选项和自由行动逐幕发展，并在之后打开存档继续游玩。

目前是可运行的原型版本，重点是打通「设定准备 → 创建故事 → 互动推进 → 自动保存 → 继续游玩」。项目同时保留了早期的多章节小说生成接口。

## 当前功能

- **独立设定库**：分别创建、导入、编辑世界书与人设卡，供不同故事复用。
- **玩家本人**：直接填写文字身份，或选用、导入、手写一张详细人设卡。
- **关键 NPC**：添加同伴、对手等重要人物，由 AI 根据设定演绎，也可以在后续剧情中补充。
- **文字互动**：选择推荐行动，或自由输入自己的行动；支持 `Ctrl + Enter` 发送。
- **状态与记忆**：显示当前位置、物品、目标等可见状态，保存累计剧情摘要。
- **自动存档**：每幕生成成功后保存正文、状态和记忆，刷新后可以从「我的故事」继续。
- **中途调整设定**：在「管理故事设定」中补充世界条目、角色和文风，从下一幕开始使用。
- **重试与冲突检查**：重复的创建、行动请求不会重复推进存档；旧版本操作会提示重新读取。

## 快速开始

### 1. 首次准备环境

以下命令以 **Windows + PowerShell** 为例，默认从项目根目录执行。先安装 Python、Node.js 和 pnpm。

创建后端虚拟环境并安装依赖：

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

安装前端依赖：

```powershell
Push-Location frontend
pnpm install
Pop-Location
```

从示例配置创建 `.env`。已有配置时会跳过，避免覆盖：

```powershell
if (!(Test-Path -LiteralPath .env)) {
    Copy-Item -LiteralPath .env.example -Destination .env
}
```

打开根目录 `.env`，填写文本模型 API 配置：

```dotenv
DEEPSEEK_API_KEY=填写你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
```

`DEEPSEEK_MODEL` 是仓库中的默认配置值；请按实际使用的服务和账号填写可用模型名。密钥只保存在后端配置中，不要放入 `VITE_` 开头的变量。

**当前互动游戏流程不需要启动 Ollama。** Ollama 与 Chroma 检索用于保留的小说生成流程，后文单独说明。

### 2. 一键启动

双击根目录的 **`start_novelagent.cmd`**。

启动入口会检查现有环境，启动前后端，等待服务就绪后打开浏览器：

- 游戏页面：[http://127.0.0.1:5173/](http://127.0.0.1:5173/)
- 后端接口文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 后端健康检查：[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

游玩期间保留启动窗口，按 `Ctrl+C` 停止服务。重复双击时，如果检测到已有的 NovelAgent 实例，会打开现有页面；其他程序占用端口时会显示错误提示。

入口使用已有的后端虚拟环境和前端依赖，不会自动安装软件。它会从 PATH 及常见的 NVM for Windows 安装目录查找可用 Node.js，不修改系统设置。

一键入口默认关闭后端自动重载。更新后端代码或 `.env` 后，请先停止原来的服务，再重新启动；重复双击打开现有实例不会重新加载配置。

### 3. 开始第一段故事

1. 点击「新故事」，准备世界书；也可以点击「填入示例」。
2. 在「玩家本人」中填写身份，或选择一张人设卡。选卡后无需重复填写文字身份。
3. 按需添加「关键 NPC」，也可以留空，之后随剧情补充。
4. 填写故事名称，并按需设置开场情境与文风。
5. 点击「开始我的故事」，等待生成开场。
6. 通过推荐选项或自由输入行动继续游玩。

每幕完成后自动保存。再次访问页面时，从「我的故事」打开存档即可继续。

## 世界书、人设卡与故事的关系

### 世界书：定义背景与规则

世界书用于描述时代、地理、势力、世界规则、禁忌和背景人物等。可以手动编辑条目，也可以从文件导入。

每个条目支持：

- 标题与正文。
- 启用或停用。
- 常驻设定。
- 关键词触发；关键词为空时按常驻处理。

关键词匹配会参考本次行动、玩家身份、开场要求、近期剧情、当前状态和累计记忆。它是当前项目的简化规则，不代表完整复现酒馆的世界书引擎。

### 人设卡：定义一个人物

人设卡包含姓名、身份与外貌、性格、背景、目标，以及可选的情境、开场白和对白示例。导入时也会保留支持的角色关联世界书。

在故事中，人设卡按用途分为：

| 用途 | 谁来扮演 | 使用方式 |
| --- | --- | --- |
| 玩家本人 | 用户 | 作为玩家身份，行动与重大选择由用户决定 |
| 关键 NPC | AI | 按人物设定和已发生剧情进行演绎 |

玩家身份使用文字描述或启用的玩家卡其中一种来源。选择或更换玩家卡不会移除已经添加的 NPC。新添加的 NPC 会提供给叙事模型，实际出场仍由剧情衔接。

### 设定库：保存可复用模板

「设定库」中的世界书与人设卡独立保存，可以用于多个故事。卡片在库中不固定为玩家或 NPC，选入具体故事时再确定用途。

**故事使用的是设定副本。** 修改设定库中的模板不会自动影响已有存档；要调整某个故事，请进入该故事的「管理故事设定」。

故事中的世界书、人物卡和文字身份，也可以另存回设定库，作为新的模板使用。

### 游玩中继续补充

打开存档 → 点击「管理故事设定」→ 添加或编辑世界书与角色 → 保存并继续故事。

更新后的设定用于下一幕，不会重写已经保存的正文、状态或累计记忆。涉及过去事实的冲突，当前由模型尝试合理衔接，没有自动修订历史剧情的功能。

## 导入格式与测试素材

文件请使用 **UTF-8 编码**。

| 内容 | 支持的格式 | 导入行为 |
| --- | --- | --- |
| 世界书 | TXT、Markdown | 整篇作为一条常驻设定，不会自动按标题拆分 |
| 世界书 | 酒馆世界书 JSON | 接收 `entries` 数组或对象，保留正文、标题、关键词、常驻与启用标记 |
| 世界书 | 含 `character_book` 的角色卡 JSON | 提取内嵌世界书，支持外层 `data` 包装 |
| 世界书 | 原 NovelAgent 故事设定 JSON | 含 `worldview` 或 `premise` 时作为一条固定设定导入 |
| 人设卡 | TXT、Markdown | 文件名作为卡片名称，正文作为人物描述 |
| 人设卡 | 酒馆 V1 / V2 / V3 JSON | 读取支持的基础字段及内嵌世界书，不执行高级扩展 |

当前不支持 PNG 人设卡、宏替换、脚本、正则触发、概率触发和递归激活等酒馆高级机制。角色卡中的开场白作为生成参考，不会在中途添加角色时直接插入已有正文。

仓库提供两组 Markdown 测试素材：

| 题材 | 世界书 | 玩家人设卡 |
| --- | --- | --- |
| 悬疑奇幻：迷雾列车与失踪调查 | [雾钟列车](examples/test-settings/雾钟列车-世界书.md) | [沈照](examples/test-settings/沈照.md) |
| 温暖冒险：浮空岛屿与跨岛送信 | [浮岛邮局](examples/test-settings/浮岛邮局-世界书.md) | [温枝](examples/test-settings/温枝.md) |

分别导入设定库，再创建故事使用。世界书中包含推荐开场，可复制到「故事从哪里开始？」中。

## 技术栈与生成流程

| 层次 | 当前实现 |
| --- | --- |
| 前端 | Vue 3、Vite、原生 CSS |
| 后端 | Python、FastAPI、Pydantic |
| 数据存储 | SQLite、SQLModel |
| 文本生成 | OpenAI Python SDK 调用配置的 DeepSeek 兼容文本接口 |
| 游戏记忆 | 累计摘要、当前可见状态、最近四幕正文 |
| 原小说流程 | LangGraph 编排、Chroma 向量检索、Ollama `bge-m3` 嵌入 |
| 验证 | pytest、前端构建、可选模型冒烟检查 |

### 当前互动游戏流程

```text
世界书 + 玩家身份 + 关键 NPC
              ↓
本次行动 + 当前状态 + 累计记忆 + 最近四幕
              ↓
匹配相关世界书条目，组装生成上下文
              ↓
生成本幕正文、推荐行动、完整可见状态与更新后的累计摘要
              ↓
正文、状态与记忆一起写入 SQLite
              ↓
等待玩家下一次行动
```

创建开场或生成下一幕失败时，不保存半幕内容，也不推进场景编号。已有剧情按存档隔离；请求携带标识与版本信息，用于处理重试及并发修改。

游戏流程目前没有接入向量检索。长篇记忆依赖模型维护累计摘要，仍可能遗漏信息或出现前后矛盾。

### 保留的小说生成流程

早期流程仍通过 `/api/stories` 相关接口提供，原始页面组件保留在 `frontend/src/App.vue`；当前默认页面入口是 `frontend/src/GamePlatform.vue`。

小说流程为：故事想法 → 生成并确认设定 → 生成章节事件 → 生成并确认正文 → 抽取状态与摘要 → 下一章。

该流程使用 SQLite 保存正文、最新状态、状态历史和摘要；只有状态变化的自然语言描述进入 Chroma，章节正文不做向量化。

如果需要运行这套流程，再准备本地嵌入服务：

```powershell
ollama pull bge-m3
ollama serve
```

如果 Ollama 已在运行，不必重复启动。模型实际名称为 `bge-m3:latest` 等其他名称时，请相应修改 `.env` 中的 `OLLAMA_EMBEDDING_MODEL`。

## 配置说明

完整配置示例见 [`.env.example`](.env.example)。

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 空 | 文本生成所需密钥 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 文本接口地址 |
| `DEEPSEEK_MODEL` | `deepseek-flash` | 模型名，以实际服务支持为准 |
| `MODEL_TIMEOUT_SECONDS` | `120` | 后端模型请求超时秒数 |
| `MODEL_MAX_RETRIES` | `1` | 模型请求额外重试次数 |
| `VITE_API_TIMEOUT_MS` | `300000` | 前端请求超时毫秒数 |
| `VITE_API_BASE` | `http://127.0.0.1:8000` | 前端连接的后端地址，可按需添加 |
| `DATABASE_URL` | `sqlite:///data/story.db` | 数据库位置 |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | 原小说流程的本地嵌入服务 |
| `OLLAMA_EMBEDDING_MODEL` | `bge-m3` | 原小说流程的嵌入模型 |
| `CHROMA_PATH` | `data/chroma` | 原小说流程的向量数据目录 |

使用一键入口或 `scripts/dev_start.py` 时，根目录 `.env` 会传给后端，只有 `VITE_` 开头的配置会额外传给前端。手动启动 Vite 时，根目录 `.env` 不会由该脚本传入；有自定义前端配置时，需自行设置对应环境变量。

### 数据位置与备份

默认情况下，故事存档、设定库、正文、状态与累计记忆都保存在项目根目录的 `data/story.db`。原小说流程的向量数据保存在 `data/chroma/`。

备份前先停止服务，再复制数据库文件；需要保留小说检索数据时，一并备份 `data/chroma/`。清除浏览器缓存不会删除后端数据库中的存档。

## 开发与验证

### 启动开发服务

在项目根目录执行以下命令，可同时启动前后端并打开网页；后端默认启用自动重载：

```powershell
backend\.venv\Scripts\python.exe scripts\dev_start.py --open
```

也可以在两个终端中分别启动。

后端：

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

前端：

```powershell
Push-Location frontend
pnpm dev --host 127.0.0.1 --port 5173
Pop-Location
```

### 无需真实模型的检查

后端测试使用替代模型客户端，不需要真实文本接口或运行中的 Ollama：

```powershell
$env:PYTHONPATH = "backend"
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
backend\.venv\Scripts\python.exe -m compileall backend\app backend\tests backend\scripts
```

前端构建：

```powershell
Push-Location frontend
pnpm build
Pop-Location
```

游戏接口测试覆盖世界书和人设卡导入、模板副本隔离、存档恢复、重复请求、失败重试、中途更新设定，以及生成与设定修改冲突等场景。

### 原小说流程的额外检查

以下脚本会检查或调用真实服务，需要相应配置：

```powershell
backend\.venv\Scripts\python.exe backend\scripts\check_ollama.py
backend\.venv\Scripts\python.exe backend\scripts\smoke_check.py
```

真实文本 API 冒烟检查需在 `backend` 目录运行，会实际调用配置的模型：

```powershell
Push-Location backend
.\.venv\Scripts\python.exe scripts\api_smoke.py
Pop-Location
```

`scripts/demo_check.ps1` 会同时检查 Ollama、运行后端测试与编译、构建前端；追加 `-RunApiSmoke` 会调用真实文本模型。它服务于包含原小说能力的完整检查，**不是体验当前互动游戏的必需步骤**。

## 主要接口

详细请求与响应结构以运行中的 [FastAPI 接口文档](http://127.0.0.1:8000/docs) 为准。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| POST | `/api/worldbooks/import` | 解析世界书文件内容 |
| POST | `/api/characters/import` | 解析人设卡文件内容 |
| GET / POST | `/api/library/worldbooks` | 列出或新建世界书模板 |
| PUT | `/api/library/worldbooks/{id}` | 更新世界书模板 |
| GET / POST | `/api/library/characters` | 列出或新建人设卡模板 |
| PUT | `/api/library/characters/{id}` | 更新人设卡模板 |
| GET / POST | `/api/games` | 列出存档或创建游戏开场 |
| GET | `/api/games/{id}` | 读取存档及完整场景历史 |
| POST | `/api/games/{id}/actions` | 提交行动并生成下一幕 |
| PUT | `/api/games/{id}/settings` | 更新当前存档的设定 |

创建和行动请求携带 `request_id`。行动请求同时携带 `expected_version` 与 `expected_settings_revision`；设定更新也携带这两个版本字段。收到 `409` 表示页面中的存档或设定已过期，应重新读取后再操作。

## 目录结构

```text
NovelAgent/
├─ start_novelagent.cmd           # Windows 一键启动入口
├─ .env.example                  # 配置示例
├─ backend/
│  ├─ app/
│  │  ├─ api/                    # 游戏、设定库与原小说接口
│  │  ├─ schemas/                # 请求与响应结构
│  │  ├─ services/               # 游戏生成、导入、记忆与设定库逻辑
│  │  ├─ storage/                # 数据表、SQLite 与向量存储
│  │  ├─ agents/                 # 原小说流程的规划、写作与记忆角色
│  │  ├─ retrieval/              # 原小说流程的检索与上下文组装
│  │  └─ workflows/              # 原小说流程的 LangGraph 编排
│  ├─ scripts/                   # 模型与接口冒烟检查
│  └─ tests/                     # 后端测试
├─ frontend/
│  └─ src/
│     ├─ GamePlatform.vue        # 当前游戏平台主页面
│     ├─ components/             # 世界书、人物卡与故事角色编辑器
│     ├─ api/                    # 后端请求封装
│     └─ styles/                 # 页面样式
├─ examples/test-settings/        # 可导入的 Markdown 测试素材
├─ scripts/                      # 开发启动与检查脚本
└─ data/                         # 本地运行数据
```

## 当前限制

- 以本地个人使用为主，没有账号、权限隔离或面向公网的部署支持；同一后端的访问者共享设定库与存档列表。
- 行动结果由模型判断，尚无独立的数值结算或确定性规则引擎。
- 尚无剧情分支回退、完整版本回滚、社区发布或多媒体演出功能。
- 游戏记忆使用累计摘要与近期正文，尚未验证长篇持续游玩的稳定性。
- 世界书与角色设定会约束生成，但不能保证模型始终遵守全部规则或保守全部秘密。
- 当前触发的单本世界书内容上限为 18000 字符；本回合启用的世界书和角色设定合计另有 30000 字符限制。超限会提示精简或停用部分设定。

## 常见问题

**双击后提示缺少 Python 环境或前端依赖？**

先完成首次环境准备。一键入口依赖 `backend/.venv/` 和 `frontend/node_modules/` 已存在。

**提示没有可用 Node.js，或出现 “No active Node.js version”？**

先确认 Node.js 已安装并可用；使用 NVM 时，确认已有安装版本并按其使用方式激活。一键入口会额外尝试常见 NVM 安装目录；手动运行 pnpm 仍需要终端中的 Node.js 配置正常。

**提示端口已被占用？**

检查是否已有启动窗口。已有完整 NovelAgent 实例时可直接打开页面；其他进程占用端口时，先处理占用再启动。

**生成超时或接口报错？**

检查 `.env` 中的密钥、接口地址与模型名是否匹配实际服务，并查看后端窗口中的错误。模型响应较慢时可适当调整前后端超时配置。失败后可重试；在生成完成前不要反复新建请求。

**修改设定库后，为什么正在玩的故事没变化？**

已有故事保存独立副本。请在该故事中打开「管理故事设定」，编辑或追加内容后保存。

**为什么 Markdown 导入后只有一个条目？**

当前把文本文件整体作为一条设定，Markdown 标题只保留为正文。需要关键词触发时，请手动拆分条目并设置关键词，或导入结构化世界书 JSON。
