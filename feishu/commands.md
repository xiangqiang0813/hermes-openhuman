# 常用飞书CLI命令速查

## 个人信息查询

- **查看自己的用户信息**
  ```bash
  lark-cli contact +get-user
  ```

## 日程管理

- **获取今日日程安排**
  ```bash
  lark-cli calendar +agenda
  ```

## 任务系统

- **获取我的所有任务**
  ```bash
  lark-cli task +get-my-tasks
  ```

## 文档管理

- **搜索文档内容**
  ```bash
  lark-cli docs +search
  ```

- **创建新文档**
  ```bash
  lark-cli docs +create
  ```

## 即时通讯

- **发送消息**
  ```bash
  lark-cli im send --text "消息内容" --open-id [用户OpenID]
  ```

## 授权与状态

- **检查当前授权状态**
  ```bash
  lark-cli auth status
  ```

## 高级用法

从 Hermes 内部调用时，记得使用环境变量隔离：

```bash
env -i lark-cli contact +get-user
```

这样可以避免上下文污染，确保命令正确执行。