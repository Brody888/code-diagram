# code-diagram

> Language switcher: [中文](README.zh.md)

Generate technical diagrams, feature inventories, and code review reports from source code — language-agnostic, framework-adaptive, zero configuration.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Method 1: Claude Code](#method-1-claude-code-recommended)
  - [Method 2: Any Agent Framework](#method-2-any-agent-framework)
  - [Method 3: Manual Download](#method-3-manual-download)
  - [Dependencies](#dependencies)
- [Full Walkthrough](#full-walkthrough)
  - [Step 1: --init project detection](#step-1---init-project-detection)
  - [Step 2: --index build index](#step-2---index-build-index)
  - [Step 3: --tree call chain tracing](#step-3---tree-call-chain-tracing)
  - [Step 4: --features feature inventory](#step-4---features-feature-inventory)
  - [Step 5: --review code review](#step-5---review-code-review)
  - [Step 6: --impact change impact](#step-6---impact-change-impact)
  - [Step 7: -t generate diagrams](#step-7--t-generate-diagrams)
  - [Step 8: --error-path error tracing](#step-8---error-path-error-tracing)
- [Project Types](#project-types)
- [Output Directory](#output-directory)
- [FAQ](#faq)
- [License](#license)

---

## Features

| Command | What it does | Output | Format |
|---------|-------------|--------|--------|
| `--init` | Auto-detect project: language, build system, framework, modules, feature flags, error model | `.code-diagram.json` | JSON |
| `--index` | Build full call graph index (functions + CLI commands + public APIs + feature flags) | `code-diagram/<project>.json` | JSON |
| `--tree <func>` | Call chain tracing (3 levels deep, communication mode annotations) | stdout | Indented tree |
| `--features` | Feature inventory (5 tables: modules/features/flags/products/events) | `code-diagram/features-report.md` | Markdown / HTML |
| `--review` | Code review + risk assessment (15 checks + fix suggestions + grade) | `code-diagram/review-report.md` | Markdown / HTML |
| `--impact <symbol>` | Change impact analysis (what breaks if X changes) | stdout | Reverse dependency tree |
| `--error-path <func>` | Error propagation tracing (error origin → report destination) | stdout | Error chain |
| `-t activity <func>` | Activity diagram (function call chain → flowchart) | `.puml` → SVG + PNG | PlantUML / Mermaid |
| `-t sequence` | Sequence diagram (multi-role cross-layer messaging) | Same as above | PlantUML / Mermaid |
| `-t state` | State diagram (state machine transitions) | Same as above | PlantUML / Mermaid |
| `-t component` | Component diagram (module architecture) | Same as above | PlantUML |
| `-t er` | ER diagram (struct/data model relationships) | Same as above | PlantUML / Mermaid |
| `-t timing` | Timing waveform (parallel signal alignment) | Same as above | WaveDrom |

### Supported Languages

| Language | Auto-detection |
|----------|---------------|
| **C / C++** | Function definitions (with typedef types), `#define`/`#ifdef` flags, `add_command()` CLI registration, ISR handlers, fixed-address structs |
| **Python** | Function/class definitions, `@click.command`/`@cli.command` CLI registration, `pytest` tests, `setup.py` packages |
| **Go** | Exported functions, `cobra.Command` CLI registration, `go build -tags` flags, `go.mod` modules |
| **Rust** | `pub fn`, `#[cfg(feature = "...")]` feature flags, `Cargo.toml` |
| **Java** | public methods, `@Command` annotations, Maven/Gradle modules |

---

## Installation

### Method 1: Claude Code (Recommended)

**Prerequisite**: [Claude Code](https://claude.ai/code) installed.

```bash
# 1. Clone into Claude Code's skills directory
git clone https://github.com/Brody888/code-diagram.git ~/.claude/skills/code-diagram

# 2. Verify the skill is loaded
ls ~/.claude/skills/code-diagram/
# Should see: README.md  SKILL.md  scripts/  styles/  examples/

# 3. In Claude Code, navigate to your project directory, then:
/code-diagram --init
```

Claude Code automatically recognizes the trigger rule in `SKILL.md`: when the user types `/code-diagram`, this skill is invoked.

### Method 2: Any Agent Framework

Works with OpenCode, Hermes, Cline, Continue, or any AI coding assistant that can execute shell commands.

```bash
# 1. Clone anywhere
git clone https://github.com/Brody888/code-diagram.git ~/tools/code-diagram
cd ~/tools/code-diagram

# 2. Check Python version (3.9+ required)
python3 --version
# Python 3.12.x ✓

# 3. Inject SKILL.md content as system prompt into your agent
#    Then call scripts/ directly:

# Project detection
python3 scripts/init-project.py /path/to/your/project

# Build index
python3 scripts/build-index.py --project /path/to/your/project

# Feature inventory (Markdown)
python3 scripts/features-report.py --project /path/to/your/project

# Feature inventory (HTML)
python3 scripts/features-report.py --project /path/to/your/project --html

# Code review
python3 scripts/generate-review-report.py --project /path/to/your/project
```

### Method 3: Manual Download

```bash
# Download latest release
curl -L https://github.com/Brody888/code-diagram/releases/latest/download/code-diagram.tar.gz | tar xz
cd code-diagram

# Verify
python3 scripts/build-index.py --help
```

### Dependencies

| Tool | Purpose | Required? |
|------|---------|-----------|
| **Python 3.9+** | Index building, feature discovery, code review | ✅ Required |
| `plantuml` | Activity/sequence/ER diagram SVG rendering | Optional |
| `cairosvg` | PNG export (recommended) | Optional |
| `rsvg-convert` | PNG export (fallback) | Optional |
| `mmdc` | Mermaid diagram SVG rendering | Optional |
| `wavedrom-cli` | WaveDrom SVG rendering | Optional |

**macOS**:

```bash
brew install plantuml librsvg python
pip install cairosvg
```

**Linux (Debian/Ubuntu)**:

```bash
sudo apt update
sudo apt install -y plantuml librsvg2-bin python3 python3-pip
pip install cairosvg
```

**Linux (RHEL/Fedora)**:

```bash
sudo dnf install -y plantuml librsvg2-tools python3 python3-pip
pip install cairosvg
```

**Windows (PowerShell)**:

```powershell
# Python (if not already installed)
winget install Python.Python.3.12

# PlantUML (requires Java)
winget install Oracle.JavaRuntimeEnvironment
# Download plantuml.jar from https://plantuml.com/download
# Or use Chocolatey:
choco install plantuml

# CairoSVG
pip install cairosvg

# rsvg-convert (via Chocolatey)
# choco install rsvg-convert
```

> Skip diagram rendering entirely by adding `--no-png`:
> ```bash
> /code-diagram -t activity my_func --no-png
> ```

### Platform-specific Paths

| Platform | Claude Code skills directory |
|----------|----------------------------|
| macOS / Linux | `~/.claude/skills/code-diagram` |
| Windows | `%USERPROFILE%\.claude\skills\code-diagram` |

```powershell
# Windows: clone into Claude Code skills directory
git clone https://github.com/Brody888/code-diagram.git $env:USERPROFILE\.claude\skills\code-diagram
```

---

## Full Walkthrough

Examples use a fictional project **`task-scheduler`** (Go REST service + CLI tool):

```
task-scheduler/
├── cmd/scheduler/main.go     # CLI entry point
├── internal/
│   ├── api/                   # HTTP handlers
│   ├── scheduler/             # Scheduling engine
│   ├── queue/                 # Message queue
│   └── db/                    # Database layer
├── config/
│   └── config.go              # Configuration + feature flags
├── go.mod
└── go.sum
```

### Step 1: `--init` Project Detection

```bash
/code-diagram --init
```

**Output**:

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

Generated `.code-diagram.json`:

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

### Step 2: `--index` Build Index

```bash
/code-diagram --index
```

**Output**:

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

### Step 3: `--tree` Call Chain Tracing

```bash
/code-diagram --tree schedule_task
```

**Output**:

```
Call chain tree (3 levels):
  schedule_task()  [scheduler: scheduler.go:142]
  ├── validateTask()        [scheduler: validator.go:28]
  ├── db.InsertTask()       [rpc → database]
  │   └── db.conn.ExecContext()  [sql driver]
  ├── queue.Enqueue()       [event → message broker]
  │   └── rabbitmq.Publish()  [amqp]
  └── api.respondJSON()     [http → client]
      └── json.Marshal()    [stdlib]

Branches: task invalid → 400, db fail → 500 + rollback
Loops:    none
Comm:     rpc(1) + event(1) + http(1)
```

### Step 4: `--features` Feature Inventory

```bash
/code-diagram --features
```

**Output** (full report written to `code-diagram/features-report.md`):

```
## Table 1 — Module Overview
| Module     | Functions | Role |
|------------|-----------|------|
| scheduler  | 34        | Scheduling engine core |
| api        | 28        | REST API handlers |
| queue      | 18        | Message queue adapters |
| db         | 22        | Database layer |
| cmd        | 15        | CLI entry + config |

## Table 2 — Feature Detail
| Module    | Feature          | Entry Point         | Comm    |
|-----------|-----------------|---------------------|---------|
| scheduler | Task scheduling  | schedule_task()     | db, event |
| scheduler | Task retry       | retry_failed()      | db, event |
| api       | Create task      | handleCreateTask()  | http    |
| api       | Query status     | handleGetStatus()   | http    |
| queue     | Message enqueue  | Enqueue()           | event   |
| ...       | ...             | ...                 | ...     |

## Table 3 — Feature Switches (15 total)
| Flag                    | Default | Description         |
|-------------------------|---------|---------------------|
| ENABLE_RETRY            | true    | Retry on failure    |
| MAX_RETRY_COUNT         | 3       | Max retry attempts  |
| QUEUE_BACKEND           | rabbitmq| Queue backend       |
| DB_MAX_CONNECTIONS      | 100     | DB connection pool  |
| ENABLE_GRACEFUL_SHUTDOWN| true    | Graceful shutdown   |
| ...                     | ...     | ...                 |

Stats: 5 modules | 386 indexed | 15 switches | GOD NODE: db.ExecContext() (47 callers)
```

**Generate HTML report**:

```bash
/code-diagram --features --html
# → code-diagram/features-report.html
```

### Step 5: `--review` Code Review

```bash
/code-diagram --review
```

**Output**:

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

**HTML report** (`--html`):

```
/code-diagram --review --html
# → code-diagram/review-report.html
```

### Step 6: `--impact` Change Impact

```bash
/code-diagram --impact task_config
```

**Output**:

```
task_config impact scope:
  ┌─ 🟡 Medium: referenced by 12 functions
  │
  ├─ Direct references:
  │   ├── config.Load()        [config: config.go:45]
  │   ├── main()               [cmd: main.go:28]
  │   └── scheduler.Init()     [scheduler: scheduler.go:65]
  │
  ├─ Field-level references:
  │   ├── MaxRetries        → retry_failed()
  │   ├── QueueBackend      → queue.New()
  │   └── DBMaxConnections  → db.NewPool()
  │
  └─ Indirect (via config.Get()):
      └── 12 files across 4 modules
```

### Step 7: `-t` Generate Diagrams

#### Activity Diagram

```bash
/code-diagram -t activity schedule_task
```

Generates `schedule_task_flow.puml`, auto-rendered to SVG + PNG. Includes: 3 partitions (scheduler / queue / db), conditional branches (task valid? / db ok?), communication annotations ([rpc] [event] [http]).

#### Sequence Diagram

```bash
/code-diagram -t sequence schedule_task
```

Generates API → Scheduler → DB → Queue cross-service message flow with 4-color arrows (rpc / db / event / http).

#### ER Diagram

```bash
/code-diagram -t er task_config
```

Generates struct relationship diagram: `TaskConfig` → embeds `QueueConfig`/`DBConfig` → references `RetryPolicy`.

#### Mermaid Lightweight

```bash
/code-diagram --mermaid -t flow retry_failed
```

Outputs inline ` ```mermaid ` code block. Auto-recommended when node count ≤ 15.

#### WaveDrom Timing

```bash
/code-diagram -t timing retry_timeline
```

Generates retry timing waveform (4 channels: attempt / wait / process / done).

### Step 8: `--error-path` Error Tracing

```bash
/code-diagram --error-path schedule_task
```

**Output**:

```
Error propagation path (schedule_task):
  schedule_task()  [scheduler.go:142]
  ├── [err] task invalid → http.StatusBadRequest
  ├── [err] db insert fail
  │   ├── tx.Rollback()
  │   └── http.StatusInternalServerError + slog.Error()
  └── [err] queue publish fail
      ├── compensating: db.DeleteTask(id)
      └── http.StatusServiceUnavailable + alerting.PagerDuty()

Error code classification:
  ErrTaskInvalid      → 400 (client error)
  ErrDBUnavailable    → 500 (database unavailable)
  ErrQueueUnavailable → 503 (queue unavailable, compensation triggered)
```

---

## Project Types

`--init` auto-detects and matches a preset. The preset determines which review checks and semantic annotations are applied.

| Preset | Detection Signals | Specific Checks | Example |
|--------|------------------|-----------------|---------|
| **embedded-firmware** | ISR + MMIO + `while(1)` + `0x...` addresses | Polling timeout, fixed-address structs, ISR polling | Device drivers, MCU firmware |
| **rest-service** | HTTP router + DB driver + middleware | Connection pool exhaustion, SQL injection, graceful shutdown, unclosed connections | `task-scheduler` |
| **cli-tool** | `add_command` / cobra / argparse | Argument validation, stderr error output | CLI tools |
| **library** | No `main()`, many public APIs | API stability, breaking change impact | SDKs, frameworks |
| **general** | None of the above | R1/R2/R5/R7/R8 common checks | General projects |

---

## Output Directory

```
<project root>/
├── .code-diagram.json          # --init configuration
└── code-diagram/
    ├── <project>.json           # --index full call graph
    ├── features-report.md       # --features report
    ├── features-report.html     # --features --html
    ├── review-report.md         # --review report
    ├── review-report.html       # --review --html
    └── *.puml / *.svg / *.png   # -t generated diagrams
```

---

## FAQ

### Q: `--index` scanned toolchain/vendor directories?

Toolchain paths are auto-excluded (`*/lib/gcc/*`, `*/include/c++/*`, etc.). For additional exclusions, configure `exclude_dirs` in `.code-diagram.json`.

### Q: `--features` shows too few functions or API count = 0?

Check `.code-diagram.json` `preset` is correct. If it's `general` but your project is a Go REST service, manually set `"preset": "rest-service"` and rebuild the index.

### Q: How to switch between fast (index) and slow (grep) scan?

```bash
/code-diagram --tree func             # Default: index hit → fast (ms)
/code-diagram --tree func --no-cache  # Force slow scan (grep source)
```

### Q: PlantUML rendering fails?

```bash
plantuml -version               # Minimum 1.2024.x
brew upgrade plantuml           # Upgrade
plantuml -I <skill-dir>/styles -tsvg file.puml  # Specify include path
```

### Q: Can this run in CI?

Yes. `scripts/` Python scripts use only stdlib.

```yaml
# GitHub Actions example
- name: Code Review
  run: |
    python3 scripts/build-index.py --project .
    python3 scripts/generate-review-report.py
```

---

## License

MIT
