# code-diagram

> 语言切换: [English](README.md)

从源码自动生成技术图、功能清单、代码审查报告。语言无关、框架自适应——不需要手动配置。

---

## 目录

- [功能概览](#功能概览)
- [安装](#安装)
  - [方法 1：Claude Code](#方法-1claude-code推荐)
  - [方法 2：任意 Agent 框架](#方法-2任意-agent-框架)
  - [方法 3：手动下载](#方法-3手动下载)
  - [依赖说明](#依赖说明)
- [完整使用示例](#完整使用示例)
  - [Step 1: --init 项目检测](#step-1---init-项目检测)
  - [Step 2: --index 构建索引](#step-2---index-构建索引)
  - [Step 3: --tree 调用链追踪](#step-3---tree-调用链追踪)
  - [Step 4: --features 功能清单](#step-4---features-功能清单)
  - [Step 5: --review 代码审查](#step-5---review-代码审查)
  - [Step 6: --impact 变更影响](#step-6---impact-变更影响)
  - [Step 7: -t 生成技术图](#step-7--t-生成技术图)
  - [Step 8: --error-path 错误传播](#step-8---error-path-错误传播)
- [支持的项目类型](#支持的项目类型)
- [输出目录](#输出目录)
- [常见问题](#常见问题)
- [License](#license)

---

## 功能概览

| 命令 | 做什么 | 输出位置 | 输出格式 |
|------|--------|---------|---------|
| `--init` | 自动检测项目：语言、构建系统、框架、模块结构、开关宏、错误模型 | `<项目根>/.code-diagram.json` | JSON |
| `--index` | 构建全量调用图索引（函数定义 + CLI 命令 + 公共 API + 开关宏） | `<项目根>/code-diagram/<project>.json` | JSON |
| `--tree <func>` | 调用链树追踪（递归 3 层，标注通信模式） | 终端 stdout | 缩进树 |
| `--features` | 项目功能清单（5 表：模块/功能/开关/产品/中断） | `code-diagram/features-report.md` | Markdown / HTML |
| `--review` | 代码审查 + 风险评估（15 项检查 + Fix 建议 + Grade） | `code-diagram/review-report.md` | Markdown / HTML |
| `--impact <symbol>` | 变更影响分析（改了 X 影响什么） | 终端 stdout | 反向依赖树 |
| `--error-path <func>` | 错误传播路径（错误产生→上报终点） | 终端 stdout | 错误链 |
| `-t activity <func>` | 活动图（函数调用链→流程图） | `code-diagram/*.puml` → `.svg` + `.png` | PlantUML / Mermaid |
| `-t sequence` | 时序图（多角色跨层消息） | 同上 | PlantUML / Mermaid |
| `-t state` | 状态图（状态机迁移） | 同上 | PlantUML / Mermaid |
| `-t component` | 组件图（模块分层架构） | 同上 | PlantUML |
| `-t er` | ER 图（struct/数据模型关系） | 同上 | PlantUML / Mermaid |
| `-t timing` | 时序波形（并行信号对齐） | 同上 | WaveDrom |

### 支持的语言

| 语言 | 自动检测 |
|------|---------|
| **C / C++** | 函数定义（含 typedef 类型）、`#define`/`#ifdef` 开关宏、`add_command()` CLI 注册、ISR handler、固定地址 struct |
| **Python** | 函数/类定义、`@click.command`/`@cli.command` CLI 注册、`pytest` 测试、`setup.py` 包结构 |
| **Go** | 导出函数、`cobra.Command` CLI 注册、`go build -tags` 开关、`go.mod` 模块 |
| **Rust** | `pub fn`、`#[cfg(feature = "...")]` 特性开关、`Cargo.toml` |
| **Java** | public methods、`@Command` 注解、Maven/Gradle 模块 |

---

## 安装

### 方法 1：Claude Code（推荐）

**前提**：已安装 [Claude Code](https://claude.ai/code)。

```bash
# 1. 克隆到 Claude Code 的 skills 目录
git clone https://github.com/Brody888/code-diagram.git ~/.claude/skills/code-diagram

# 2. 确认 skill 已加载
ls ~/.claude/skills/code-diagram/
# 应看到: README.md  SKILL.md  scripts/  styles/  examples/

# 3. 在 Claude Code 中进入你的项目目录，然后：
/code-diagram --init
```

安装后 Claude Code 会自动识别 `SKILL.md` 中的触发规则：当用户输入 `/code-diagram` 时调用此 skill。

### 方法 2：任意 Agent 框架

适用于 OpenCode、Hermes、Cline、Continue 等任何可以执行 shell 命令的 AI 编码助手。

```bash
# 1. 克隆到任意位置
git clone https://github.com/Brody888/code-diagram.git ~/tools/code-diagram
cd ~/tools/code-diagram

# 2. 确认 Python 版本 (需要 3.9+)
python3 --version
# Python 3.12.x ✓

# 3. 将 SKILL.md 的内容作为 system prompt 注入你的 agent
#    然后直接调用 scripts/ 目录下的脚本：

# 项目检测
python3 scripts/init-project.py /path/to/your/project

# 索引构建
python3 scripts/build-index.py --project /path/to/your/project

# 功能清单 (Markdown)
python3 scripts/features-report.py --project /path/to/your/project

# 功能清单 (HTML 交互报告)
python3 scripts/features-report.py --project /path/to/your/project --html

# 代码审查
python3 scripts/generate-review-report.py --project /path/to/your/project
```

### 方法 3：手动下载

```bash
# 下载最新版本
curl -L https://github.com/Brody888/code-diagram/releases/latest/download/code-diagram.tar.gz | tar xz
cd code-diagram

# 验证
python3 scripts/build-index.py --help
```

### 依赖说明

| 工具 | 用途 | 必须？ | 安装方式 |
|------|------|--------|---------|
| **Python 3.9+** | 索引构建、功能发现、代码审查 | ✅ 必须 | 系统自带 或 `brew install python` |
| `plantuml` | 活动图/时序图/ER 图 SVG 渲染 | 可选 | `brew install plantuml` |
| `cairosvg` | PNG 导出（推荐） | 可选 | `pip install cairosvg` |
| `rsvg-convert` | PNG 导出（备选） | 可选 | `brew install librsvg` |
| `mmdc` | Mermaid 图 SVG 渲染 | 可选 | `npm install -g @mermaid-js/mermaid-cli` |
| `wavedrom-cli` | WaveDrom 波形图 SVG 渲染 | 可选 | `npm install -g wavedrom-cli` |

```bash
# macOS 一键安装全部可选依赖
brew install plantuml librsvg python
pip install cairosvg

# 如果不需要 PNG 导出，可以跳过所有可选依赖：
/code-diagram -t activity process_job --no-png   # 只生成 .puml 源文件
```

---

## 完整使用示例

以下示例基于一个虚拟项目 **`task-scheduler`**（Go 语言 REST 服务 + CLI 工具）：

```
task-scheduler/
├── cmd/scheduler/main.go     # CLI 入口
├── internal/
│   ├── api/                   # HTTP handler
│   ├── scheduler/             # 调度引擎
│   ├── queue/                 # 消息队列
│   └── db/                    # 数据库层
├── config/
│   └── config.go              # 配置 + feature flags
├── go.mod
└── go.sum
```

### Step 1: `--init` 项目检测

```bash
/code-diagram --init
```

**输出**：

```
Scanning: /Users/me/projects/task-scheduler

  Language: Go (.go = 85%)
  Build: go.mod
  Signal: http ✓
  Signal: cli ✓
  Signal: error_model ✓
  Preset: rest-service (detected: rest-service)

  Source dirs: ['cmd', 'internal', 'config']

✓ /Users/me/projects/task-scheduler/.code-diagram.json
```

生成的 `.code-diagram.json`：

```json
{
  "project": "task-scheduler",
  "language": "Go",
  "build_system": "go",
  "framework": "rest-service",
  "preset": "rest-service",
  "source_dirs": ["cmd/", "internal/", "config/"],
  "signals": ["http", "cli", "error_model"]
}
```

### Step 2: `--index` 构建索引

```bash
/code-diagram --index
```

**输出**：

```
  Types: 22 base + 18 discovered = 40 total
  Functions: 386
  CLI commands: 12 (cobra.Command pattern)
  Public APIs: 47 (location scoring)
  Switches: 15 (go build tags + config flags)
  Products: 0

✓ task-scheduler/code-diagram/task-scheduler.json
  386 funcs | 12 CLI | 47 APIs | 15 switches
```

### Step 3: `--tree` 调用链追踪

```bash
/code-diagram --tree schedule_task
```

**输出**：

```
调用链树 (3层):
  schedule_task()  [scheduler: scheduler.go:142]
  ├── validateTask()        [scheduler: validator.go:28]
  ├── db.InsertTask()       [rpc → database]
  │   └── db.conn.ExecContext()  [sql driver]
  ├── queue.Enqueue()       [event → message broker]
  │   └── rabbitmq.Publish()  [amqp]
  └── api.respondJSON()     [http → client]
      └── json.Marshal()    [stdlib]

分支:  task invalid → return 400
       db insert fail → return 500 + rollback
循环:  无
通信:  rpc(1) + event(1) + http(1)
```

### Step 4: `--features` 功能清单

```bash
/code-diagram --features
```

**输出**（完整报告写入 `code-diagram/features-report.md`）：

```
## 表 1 — Module Overview
| Module     | 函数数 | 职责 |
|------------|--------|------|
| scheduler  | 34     | 调度引擎核心 |
| api        | 28     | REST API handler |
| queue      | 18     | 消息队列适配 |
| db         | 22     | 数据库层 |
| cmd        | 15     | CLI 入口 + 配置 |

## 表 2 — Feature Detail
| Module    | 功能           | 入口函数            | 通信    |
|-----------|---------------|--------------------|---------|
| scheduler | 任务调度       | schedule_task()   | db, event |
| scheduler | 任务重试       | retry_failed()    | db, event |
| api       | 创建任务       | handleCreateTask()| http    |
| api       | 查询状态       | handleGetStatus() | http    |
| queue     | 消息入队       | Enqueue()         | event   |
| ...       | ...           | ...               | ...     |

## 表 3 — Feature Switches (15 total)
| 开关                    | 默认值 | 作用           |
|-------------------------|--------|---------------|
| ENABLE_RETRY            | true   | 失败重试       |
| MAX_RETRY_COUNT         | 3      | 最大重试次数   |
| QUEUE_BACKEND           | rabbitmq| 队列后端选择  |
| DB_MAX_CONNECTIONS      | 100    | 数据库连接池   |
| ENABLE_GRACEFUL_SHUTDOWN| true   | 优雅关闭      |
| ...                     | ...    | ...           |

统计: 5 modules | 386 indexed | 15 switches | GOD NODE: db.ExecContext() (47 callers)
```

**生成 HTML 交互报告**：

```bash
/code-diagram --features --html
# → code-diagram/features-report.html
```

### Step 5: `--review` 代码审查

```bash
/code-diagram --review
```

**输出**：

```
Code Review — task-scheduler
Grade: B+  |  🔴2 🟡4 ⚠0

🔴 R2: High Blast Radius (2 findings)
  db.ExecContext() — 47 callers (database bottleneck)
  config.Get()     — 12 callers (global config singleton)
  💡 Add regression tests. Consider connection pooling limits.

🟡 R1: Return Value Not Checked (2 findings)
  queue.Enqueue() in handleCreateTask() — error not checked
  💡 Add: if err := queue.Enqueue(task); err != nil { ... }

🟡 R5: Error Not Reported (1 finding)
  retry_failed() — error path missing structured logging
  💡 Add: slog.Error("retry exhausted", "task_id", id, "err", err)

🟡 R7: Deep Call Chains (1 finding)
  schedule_task → validateTask → db.ExecContext → sql.DB.conn (depth 4)
  💡 Consider flattening: inline validateTask into schedule_task
```

**HTML 报告**（`--html`）：

```
/code-diagram --review --html
# → code-diagram/review-report.html
```

### Step 6: `--impact` 变更影响

```bash
/code-diagram --impact task_config
```

**输出**：

```
task_config 影响范围:
  ┌─ 🟡 中: 被 12 个函数引用
  │
  ├─ 直接引用:
  │   ├── config.Load()        [config: config.go:45]
  │   ├── main()               [cmd: main.go:28]
  │   └── scheduler.Init()     [scheduler: scheduler.go:65]
  │
  ├─ 字段级引用:
  │   ├── MaxRetries        → retry_failed()
  │   ├── QueueBackend      → queue.New()
  │   └── DBMaxConnections  → db.NewPool()
  │
  └─ 间接影响 (via config.Get()):
      └── 12 files across 4 modules
```

### Step 7: `-t` 生成技术图

#### 活动图

```bash
/code-diagram -t activity schedule_task
```

生成 `schedule_task_flow.puml`，自动渲染 SVG + PNG。图包含：3 个 partition（scheduler / queue / db）、条件分支（task valid? / db ok?）、通信标注（[rpc] [event] [http]）。

#### 时序图

```bash
/code-diagram -t sequence schedule_task
```

生成 API → Scheduler → DB → Queue 的跨服务消息流，4 色箭头区分 rpc / db / event / http。

#### ER 图

```bash
/code-diagram -t er task_config
```

生成 struct 关系图：`TaskConfig` → 嵌入 `QueueConfig`/`DBConfig` → 引用 `RetryPolicy`。

#### Mermaid 轻量图

```bash
/code-diagram --mermaid -t flow retry_failed
```

输出内嵌 ` ```mermaid ` 代码块，≤15 节点时自动推荐 Mermaid。

#### WaveDrom 波形图

```bash
/code-diagram -t timing retry_timeline
```

生成重试时序波形（4 通道：attempt / wait / process / done）。

### Step 8: `--error-path` 错误传播

```bash
/code-diagram --error-path schedule_task
```

**输出**：

```
错误传播路径 (schedule_task):
  schedule_task()  [scheduler.go:142]
  ├── [err] task invalid → http.StatusBadRequest
  ├── [err] db insert fail
  │   ├── tx.Rollback()
  │   └── http.StatusInternalServerError + slog.Error()
  └── [err] queue publish fail
      ├── compensating: db.DeleteTask(id)
      └── http.StatusServiceUnavailable + alerting.PagerDuty()

错误码分类:
  ErrTaskInvalid      → 400 (客户端错误)
  ErrDBUnavailable    → 500 (数据库不可用)
  ErrQueueUnavailable → 503 (队列不可用，已触发补偿)
```

---

## 支持的项目类型

`--init` 自动检测并匹配 preset。Preset 决定审查检查项和语义标注。

| Preset | 检测信号 | 专属检查 | 示例项目 |
|--------|---------|---------|---------|
| **embedded-firmware** | ISR + MMIO + `while(1)` + `0x...` 地址 | 轮询 timeout, 固定地址 struct, ISR polling | 设备驱动、MCU 固件 |
| **rest-service** | HTTP router + DB driver + middleware | 连接池耗尽, SQL 注入, graceful shutdown, 未关闭连接 | `task-scheduler` 等 |
| **cli-tool** | `add_command` / cobra / argparse | 参数校验, stderr 错误输出 | 命令行工具 |
| **library** | 无 `main()`, 大量公共 API | 接口稳定性, 破坏性变更影响面 | SDK、框架 |
| **general** | 无法匹配上述 | R1/R2/R5/R7/R8 通用检查 | 通用项目 |

---

## 输出目录

```
<项目根>/
├── .code-diagram.json          # --init 生成的配置
└── code-diagram/
    ├── <project>.json           # --index 的索引 (全量调用图)
    ├── features-report.md       # --features 报告
    ├── features-report.html     # --features --html
    ├── review-report.md         # --review 报告
    ├── review-report.html       # --review --html
    └── *.puml / *.svg / *.png   # -t 生成的图
```

---

## 常见问题

### Q: `--index` 扫到了 toolchain/vendor 目录？

工具链路径会自动排除（匹配 `*/lib/gcc/*`, `*/include/c++/*` 等模式）。如果还有遗漏，在 `.code-diagram.json` 中配置 `exclude_dirs`。

### Q: `--features` 函数数太少 / API 数为 0？

检查 `.code-diagram.json` 的 `preset` 是否正确。如果 preset 是 `general` 但项目实际是 Go REST 服务，手动改为 `rest-service` 后重建索引。

### Q: 如何切换快扫描（索引）和慢扫描（grep）？

```bash
/code-diagram --tree func             # 默认: 索引存在 → 快 (毫秒)
/code-diagram --tree func --no-cache  # 强制慢扫描 (grep 源码)
```

### Q: PlantUML 渲染报错？

```bash
plantuml -version               # 最低 1.2024.x
brew upgrade plantuml           # 升级
plantuml -I <skill-dir>/styles -tsvg file.puml  # 指定 include 路径
```

### Q: 能在 CI 中使用吗？

可以。`scripts/` 下的 Python 脚本只用 stdlib。

```yaml
# GitHub Actions 示例
- name: Code Review
  run: |
    python3 scripts/build-index.py --project .
    python3 scripts/generate-review-report.py
```

---

## License

MIT
