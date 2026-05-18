# 飞书CLI安装与配置指南

## 快速开始

### 1. 安装飞书CLI

```bash
npm install -g @larksuite/cli
```

### 2. 添加到Hermes技能系统

```bash
npx skills add larksuite/cli -y -g
```

### 3. 初始化配置

创建新的飞书应用并绑定到Hermes：

```bash
lark-cli config init --new
lark-cli config bind
```

### 4. 用户授权

首次使用需要进行用户授权：

```bash
lark-cli auth login --recommend
```

如果需要扩展权限（如搜索文档功能）：

```bash
lark-cli auth login --scope "search:docs:read"
```

## 重要注意事项

从 Hermes 内部调用飞书CLI时，需要绕过上下文检测：

```bash
env -i lark-cli [command]
```

这样可以确保命令在干净的环境中执行，避免上下文污染。

## 验证安装

检查授权状态确认安装成功：

```bash
lark-cli auth status
```

如果一切正常，你应该能看到有效的访问令牌和权限列表。