# CLCI Example (embedded-firmware preset)

本目录包含 CLCI 项目的专属配置——与通用 skill 强隔离。

## 文件

| 文件 | 用途 |
|------|------|
| `clci-semantic.puml` | CLCI 专属语义宏（7 种硬件箭头 + 7 种固件形状） |
| `cmd_clci_link_flow.puml` | 活动图示例：`cmd_clci_link()` 调用链 |
| `er_clci_config.puml` | ER 图示例：`clci_config_t` struct 关系 |

## 使用

```plantuml
@startuml
!include <skill-dir>/styles/code-diagram-default.puml
!include <skill-dir>/examples/clci/clci-semantic.puml
title CLCI 流程图

REG(csr1, CLCI_CH_BIT_LOCK_CTRL0, 0x18040)
ISR_HANDLER(irq1, doorbell_handler)
csr1 ARROW_MMIO irq1
@enduml
```

## preset 配置

CLCI 项目 `--init` 自动检测到 `embedded-firmware`：

```json
{
  "preset": "embedded-firmware",
  "detect_signals": ["ISR_handler", "MMIO", "main_loop", "fixed_addr_regs"],
  "arrow_semantics": ["mmio", "mailbox", "sideband", "mainband", "irq", "dma", "state"],
  "review_checks": ["R1","R2","R3","R4","R5","R6","R7","R8"],
  "error_model": "sys_error_save(error_class, code) → DOORBELL → SOC"
}
```

## 项目对比

| 维度 | sep1_fw_v1.6.3 (固件) | clci_user_sdk (SDK) |
|------|----------------------|---------------------|
| 函数总数 | ~50 (core) | ~1,039 |
| GOD NODE | `cmd_parser` (33 edges) | `clci_msg_proc` (12 API 汇聚) |
| 产品数 | 8 | 9 |
| 通信模型 | ISR + main loop | polling (`clci_check`) |
| build | CMake + RISC-V toolchain | Makefile + build.sh |
