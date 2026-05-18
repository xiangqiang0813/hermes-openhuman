# Hermes Agent + OpenHuman 记忆增强方案

本项目在 Hermes Agent 基础上，借鉴 OpenHuman 的记忆设计思路，通过飞书CLI实现自动上下文同步的方案。专为希望减少"每次对话从头教"痛点的 Hermes Agent 用户设计。

## 主要功能

- **指纹去重记忆同步**：使用 SHA256 指纹避免重复记忆
- **飞书CLI整合**：统一文档、日历、任务、IM 数据通道
- **1小时自动更新**：定时同步最新上下文信息
- **≤4000 token 硬预算**：智能淘汰旧记忆，保持上下文精炼

## 项目结构

- [CREDITS.md](CREDITS.md) - 致谢与变更说明
- [feishu/README.md](feishu/README.md) - 飞书CLI安装配置指南
- [memory/README.md](memory/README.md) - 记忆系统详细设计
- [openhuman/README.md](openhuman/README.md) - OpenHuman兼容性分析
- [recovery/恢复手册.md](recovery/恢复手册.md) - 故障恢复指南