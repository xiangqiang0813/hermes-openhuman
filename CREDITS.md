# 致谢与变更说明

## OpenHuman

借鉴了以下核心设计思路：
- **记忆树分块**：将长对话拆分为 ≤3000 token 的分块，便于管理
- **自动轮询同步**：定时从各种数据源拉取最新信息
- **TokenJuice压缩思路**：通过智能压缩减少token使用

主要改动包括：
- 放弃 Rust 重写方案，改用 Hermes cronjob + Python 脚本实现
- 去重机制从 SQLite 改为基于 SHA256 的指纹系统
- 内存上限从"无上限"改为固定 4000 token 硬预算

## Karpathy's LLM Wiki

借鉴了结构化 Markdown 记忆文件和 AI 可读可编辑的设计理念。

关键改进：
- 从手动维护改为自动生成记忆文件
- 配合指纹去重机制，避免记忆冗余和重复

## Hermes Agent

充分利用了 Hermes 的原生能力：
- **cronjob 调度系统**：用于定时执行记忆更新任务
- **飞书网关**：提供统一的数据访问接口
- **Skill 自学机制**：支持动态添加新的记忆处理技能

这些能力都被直接利用，而非进行结构性改造。

## AI-Agents-ZH (智能体中文社区)

借鉴了以下关键设计：

- **SOUL.md（人格定义）**：借鉴了该社区关于 AI Agent 人格塑造和角色定位的思路，包括人格边界、行为守则、沟通风格的定义方式
- **Skill 体系**：参考了社区中 Skill 模块化的设计理念，将技能拆分为可独立加载、按需激活的功能单元
- **自动化场景匹配**：借鉴了社区中根据用户输入自动匹配对应技能的设计思路

主要改动：
- SOUL.md 从通用人格模板改为专用于 Hermes Agent 的务实工程师人格（数据驱动、成本意识、工程化思维）
- Skill 从社区标准格式调整为 Hermes Agent Skill.md 格式（YAML frontmatter + markdown body）
- 场景匹配从社区的手动模式改为 Hermes 的原生自动加载规则（输入关键词自动识别并加载对应技能）

---

## Feishu CLI (larksuite/cli)

作为核心数据通道，替代了 OpenHuman 复杂的118个第三方集成：
- 文档管理：lark-cli docs
- 日历事件：lark-cli calendar  
- 任务系统：lark-cli task
- 即时通讯：lark-cli im

用一个统一的飞书CLI覆盖了所有数据源，大大简化了架构。