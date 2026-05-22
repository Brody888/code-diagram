# code-diagram

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
# 应看到: README.md  SKILL.md  scripts/  styles/

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

# 3. 复制 SKILL.md 的内容作为 system prompt 注入你的 agent
#    或者直接手动调用 scripts/ 目录下的脚本：

# 索引构建
python3 scripts/build-index.py --project /path/to/your/project

# 功能清单 (Markdown)
python3 scripts/features-report.py --project /path/to/your/project

# 功能清单 (HTML 交互报告)
python3 scripts/features-report.py --project /path/to/your/project --html

# 代码审查
python3 scripts/review-report.py --project /path/to/your/project
```

### 方法 3：手动下载

```bash
# 下载最新版本
curl -L https://github.com/your-org/code-diagram/releases/latest/download/code-diagram.tar.gz | tar xz
cd code-diagram

# 验证脚本可执行
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
/code-diagram -t activity my_func --no-png   # 只生成 .puml 源文件
```

---

## 完整使用示例

以下示例基于真实的 CLCI 嵌入式固件项目 (`sep1_fw_v1.6.3`, C, bare-metal)。

### Step 1: `--init` 项目检测

```bash
/code-diagram --init
```

**实际输出**：

```
正在扫描项目...
  语言:        C (C11), RISC-V 交叉编译
  构建系统:    CMake + Makefile.cmake
  源码目录:    drivers/ (12 files), product/sep1/ (2 files), common/
  测试目录:    未检测到
  框架:        Bare-metal embedded (无 RTOS)

  模块划分:    6 个目录模块
    C1  — mainband          Mainband 状态机
    C3  — sideband/v3       Sideband 协议栈
    C6  — drivers           通用读写 + link 引擎
    C9  — clci_command.c    Mailbox 命令分发
    C10 — product/sep1/src/ 产品适配
    C16 — dwc_uart/wdt/doorbell/timer  底层驱动

  开关宏:      23 个 #define 从 config.h 提取
  中断注册:    5 个 ISR handler 从源码提取
  错误上报:    检测到 sys_error_save() + DOORBELL_TO_SOC 模式

  Preset: embedded-firmware

已生成: .code-diagram.json
```

`.code-diagram.json` 内容：

```json
{
  "project": "clci_combo",
  "language": "C",
  "build_system": "cmake",
  "framework": "bare-metal",
  "preset": "embedded-firmware",
  "source_roots": ["drivers/", "product/sep1/src/", "common/"],
  "modules": {
    "mainband": {"role": "Mainband 状态机", "dir": "drivers/mainband/"},
    "sideband": {"role": "Sideband 协议栈", "dir": "drivers/sideband/v3/"},
    "command":  {"role": "Mailbox 命令分发", "dir": "drivers/clci_command.c"}
  }
}
```

### Step 2: `--index` 构建索引

```bash
/code-diagram --index
```

**实际输出**：

```
1. Types from .c signatures: 12 → regex: 16 types
2. Functions discovered: 1,039
3. CLI commands: 26 (add_command pattern)
4. Public APIs: 82 (location scoring)
5. Modules: 6
6. Switches: 463
7. Products: 8

✓ Index: code-diagram/clci_user_sdk.json
  1039 funcs | 26 CLI | 82 APIs | 463 switches | 8 products
```

### Step 3: `--tree` 调用链追踪

```bash
/code-diagram --tree cmd_clci_link
```

**实际输出**：

```
调用链树 (4层, 20+ 函数):
  cmd_clci_link()  [C9: clci_command.c:368]
  └── sep1_link_with_int()  [C10: sep1_ram.c:542]  ← fp: clci_api.clci_link
      └── sep1_link()  [C10: sep1_ram.c:524]
          ├── clci_bitlock()  [C6: clci_link.c:499]  ← fp: clci_api.clci_bitlock
          │   ├── clci_bitlock_en()              [mmio] per die/lane
          │   ├── clci_bitlock_state_check(0x1)  [mmio] 轮询
          │   ├── clci_bitlock_state_trigger()   [mmio] ×3
          │   ├── phase0_data_check()            [mmio] 轮询
          │   ├── phase0_clock_check()           [mmio] 轮询
          │   ├── delay_line_config()            [mmio] 校准
          │   └── phase1_check()                 [mmio] 轮询 CTRL1/2
          ├── clci_pcslock()  [C6: clci_link.c:770]  ← fp: clci_api.clci_pcslock
          │   ├── pcslock_trigger()      [mmio] BER check
          │   ├── rx_fh_check()          [mmio] 轮询
          │   ├── lane_sync_check()      [mmio] 轮询
          │   ├── lane_link_check()      [mmio] 轮询
          │   └── tx_en()                [mmio] enable TX
          └── sep1_enable_mac_tx_ready() [mmio]

分支:  bitlock phase 任一 fail → sys_error_save → return
循环:  per-die, per-lane (bitlock state check / pcslock rx check)
通信:  mailbox(1) + mmio(5+bitlock phases) + irq(2 doorbell)

⏱  Index lookup: 37 functions available, no grep needed
```

### Step 4: `--features` 功能清单

```bash
/code-diagram --features
```

**终端输出**（摘要，完整报告写入 `code-diagram/features-report.md`）：

```
## 表 1 — Module Overview
| Module     | 函数数 | 职责 |
|------------|--------|------|
| mainband   | 12     | Mainband 10-state hook machine |
| sideband   | 45     | Sideband 协议栈 (4-layer)      |
| command    | 32     | Mailbox 命令分发               |
| link       | 18     | Bitlock/PCSLock 引擎           |
| platform   | 8      | 启动 + 产品适配                |
| driver     | 15     | UART/WDT/Doorbell/Timer        |

## 表 2 — Feature Detail
| Module   | 功能            | 入口函数              | 通信          |
|----------|----------------|----------------------|---------------|
| command  | CMD_CLCI_LINK  | cmd_clci_link()      | mailbox, mmio |
| command  | CMD_BITLOCK    | cmd_bitlock()        | mailbox, mmio |
| command  | CMD_RESET      | cmd_reset()          | mailbox       |
| link     | Bitlock 引擎   | clci_bitlock()       | mmio          |
| link     | PCS Lock 引擎  | clci_pcslock()       | mmio          |
| sideband | 协议栈初始化   | sideband_init()      | mmio, irq     |
| ...      | ...            | ...                  | ...           |

## 表 3 — Feature Switches (23 total)
| 宏                                     | 默认值 | 作用              |
|----------------------------------------|--------|-------------------|
| SIDEBAND_UCIE_INIT_MODE_SET_SUPPORT    | 1      | SB init HW 复位   |
| AUTO_LINK_MODE                         | 0      | 自动 Link 模式    |
| DOORBELL_MODE_ISR                      | 0      | Doorbell 中断模式 |
| SIDEBAND_MODE_ISR                      | 0      | Sideband 中断模式 |
| ...                                    | ...    | ...               |

## 表 4 — Product Variance (8 products)
| 产品 | CHIPID      | Chiplet | 特性         |
|------|-------------|---------|-------------|
| sep1 | 0x251100ab  | SP      | link+doorbell|
| otp2 | 0x250500ab  | AP      | 64 lanes    |
| slp1 | ?           | M2-SL   | Soft Link   |
| ...  | ...         | ...     | ...         |

统计: 6 modules | 37 indexed | 23 switches | 8 products | GOD NODE: cmd_parser (33 edges)
```

**生成 HTML 交互报告**：

```bash
/code-diagram --features --html
# → code-diagram/features-report.html
```

HTML 报告包含可折叠的表格、颜色标记的模块标签、GOD NODE 红框高亮。

### Step 5: `--review` 代码审查

```bash
/code-diagram --review
```

**终端输出**：

```
Code Review — clci_combo
Grade: C  |  🔴12 🟡9 ⚠1

🔴 R2: High Blast Radius (6 findings)
  sideband_drv_msg_cmd()  [C3] — 10 callers
  mbd_main_state_change() [C1] — 9 callers
  💡 Add regression test covering all callers. Commit with [HIGH-RISK] tag.

🔴 R4: Fixed-Address Structs (2 findings)
  clci_config_t @ 0x17c00 — HW 地址映射, 字段顺序不可变
  clci_die_t     @ 0x17d00 — HW 地址映射, 字段顺序不可变
  💡 Add static_assert(sizeof(X) == expected). Sync with HW CSR spreadsheet.

🟡 R5: Error Not Reported (3 findings)
  cmd_aphy_init, cmd_sphy_init, cmd_reset — 错误路径无 sys_error_save
  💡 Add: if(ret){sys_error_save(SYS_ERROR_CLASS_*, ret); return CMD_RESP_FAIL;}

🟡 R6: ISR Polling (3 findings)
  SIDEBAND_MODE_ISR=0, DOORBELL_MODE_ISR=0, UART_MODE_ISR=0
  💡 Measure worst-case polling latency. Consider ISR mode for production.

🟡 R7: Deep Call Chains (3 findings)
  cmd_soft_link (depth 6), cmd_clci_link (depth 5), cmd_combo (depth 5)
  💡 Run gcc -fstack-usage to confirm peak stack < IRQ stack reserve (2KB).

⚠ R8: FP Bindings — Single Product
  18 function pointers only bound in product/sep1/src/
  💡 Audit other 7 products for platform_clci_api_init() coverage.
```

**HTML 报告**（`--html`）：

```
/code-diagram --review --html
# → code-diagram/review-report.html
```

HTML 报告结构：
- 渐变色 header + 项目元信息
- 风险卡片：🔴12 🟡9 ⚠1 + Overall Grade **C**
- 8 个可折叠检查区域（点击标题展开/折叠）
- 每个 finding 卡片含 `💡 Suggested Fix` 折叠区——具体操作步骤
- 底部 Action Items：按优先级编号（1-5），含代码模板

### Step 6: `--impact` 变更影响

```bash
/code-diagram --impact clci_config_t
```

**实际输出**：

```
clci_config_t 影响范围:
  ┌─ 🔴 高: 固定地址 struct @ 0x17c00 (256B)
  │   字段顺序不可变更 — 与 HW CSR 映射绑定
  │   添加/删除字段需同步 HW team + clci_board.h
  │
  ├─ 直接引用 (extern clci_config):
  │   ├── platform_init()         [C10: clci_platform.c:86]
  │   ├── sideband_soft_msg_init() [C3: sideband_protocol.c:336]
  │   └── fw_info_init()          [C10: clci_platform.c:102]
  │
  ├─ 字段级引用:
  │   ├── cfg5.tracking_lane → clci_link.c:384 (delay line)
  │   ├── die[0..1]          → clci_reg_read/write() ×60+
  │   ├── sbd_soft_msg[4]    → sideband_protocol.c
  │   └── sys_exc_reg[4]     → sys_error.c
  │
  └─ 间接影响 (via clci_die_t):
      ├── clci_reg_read/write()   60+ sites
      ├── clci_set_link_status()   4 sites
      └── bitlock/pcslock 全部子函数
```

### Step 7: `-t` 生成技术图

#### 活动图

```bash
/code-diagram -t activity cmd_clci_link
```

生成 `cmd_clci_link_flow.puml`，自动渲染为 SVG (72KB) + PNG (248KB, 1920px)。

图包含：5 个 partition 分组（FW/Product/Bitlock/PCS Lock/MAC+Doorbell）、22 个源码链接、8 个决策菱形、MCU IRQ/Doorbell 语义标注。

#### 时序图

```bash
/code-diagram -t sequence cmd_clci_link
```

生成 SDK→Mailbox→FW→PHY 跨层消息交互图，7 色箭头（mmio/mailbox/sideband/irq/...）。

#### ER 图

```bash
/code-diagram -t er clci_config_t
```

生成 struct 关系图：`clci_config_t` → 嵌入 `clci_cfg2_t`/`cfg3_t`/`cfg5_t` → 包含 `clci_die_t[2]` → 引用 `clci_api_t*`。基址标注 @0x17c00。

#### Mermaid 轻量图

```bash
/code-diagram --mermaid -t flow ber_check
```

输出内嵌 Markdown 代码块，可直接放在文档中。节点数 ≤15 时自动推荐 Mermaid。

#### WaveDrom 波形图

```bash
/code-diagram -t timing clci_bitlock
```

生成 bitlock phase 推进的并行信号波形（9 通道：bitlock_en / state_check / trigger / phase0_data / phase0_clk / delay_cal / phase1）。

### Step 8: `--error-path` 错误传播

```bash
/code-diagram --error-path cmd_clci_link
```

**实际输出**：

```
错误传播路径 (cmd_clci_link):
  cmd_clci_link()  [clci_command.c:370]
  ├── [err] ret != 0
  │   ├── clci_write(die0, DOORBELL, LINK_FAIL_BIT)  [irq → SOC]
  │   └── clci_write(die1, DOORBELL, LINK_FAIL_BIT)  [irq → SOC]
  └── [err] sys_error_save(SYS_ERROR_CLASS_LINK, ret)
      └── sys_exc_reg[0..3] ← 错误快照 (64B)
          └── SOC 端: clci_get_reg(0, SYS_EXC_REG_ADDR) → 诊断日志

错误码分类:
  SYS_ERROR_CLASS_LINK       → bitlock/pcslock/link training 失败
  SYS_ERROR_CLASS_BITLOCK    → bitlock phase check 超时
  SYS_ERROR_CLASS_PCSLOCK    → pcslock rx/sync/link 超时
  SYS_ERROR_CLASS_APHY_PLL   → APHY PLL 初始化失败
```

---

## 支持的项目类型

`--init` 自动检测并匹配 preset。Preset 决定审查检查项和语义标注。

| Preset | 检测信号 | 专属检查 |
|--------|---------|---------|
| **embedded-firmware** | ISR + MMIO + `while(1)` + `0x...` 地址 | R3 轮询 timeout, R4 固定地址 struct, R6 ISR polling |
| **rest-service** | HTTP router + DB driver + middleware | R3 连接池耗尽, R4 SQL 注入, R6 graceful shutdown, R9 未关闭连接 |
| **cli-tool** | `add_command` / cobra / argparse | R1 参数校验, R5 stderr 错误输出 |
| **library** | 无 `main()`, 大量公共 API | R8 接口稳定性, R2 破坏性变更影响面 |
| **general** | 无法匹配上述 | R1/R2/R5/R7/R8 通用检查 |

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

工具链和 vendor 目录会自动排除（匹配 `*/lib/gcc/*`, `*/include/c++/*` 等模式）。如果还有遗漏，在 `.code-diagram.json` 中配置 `exclude_dirs`。

### Q: `--features` 报告里函数数太少 / API 数为 0？

这是已知的自适应算法陷阱（SKILL.md §Algorithm Heuristics H1-H15）。通常原因：
1. 项目使用了非标准类型（正则没匹配到）→ `--index` 重建索引会自动学习
2. 评分阈值不匹配项目类型 → 检查 `.code-diagram.json` 的 `preset` 是否正确
3. 运行 `--index --no-cache` 看慢扫描能否发现更多

### Q: 如何切换快扫描（索引）和慢扫描（grep）？

```bash
/code-diagram --tree func             # 默认: 索引存在 → 快 (毫秒)
/code-diagram --tree func --no-cache  # 强制慢扫描 (grep 源码, 秒级)
```

### Q: PlantUML 渲染报错？

常见原因：`!include` 路径不存在、PlantUML 版本过旧。最低版本 1.2024.x。

```bash
plantuml -version               # 检查版本
brew upgrade plantuml           # 升级
# 或者用 -I 指定 include 路径
plantuml -I <skill-dir>/styles -tsvg file.puml
```

### Q: 能在 CI 中使用吗？

可以。`scripts/` 下的 Python 脚本零外部依赖（只用 stdlib），可以直接在 CI pipeline 中调用：

```yaml
# GitHub Actions 示例
- name: Code Review
  run: |
    python3 scripts/build-index.py --project .
    python3 scripts/review-report.py
```

---

## License

MIT
