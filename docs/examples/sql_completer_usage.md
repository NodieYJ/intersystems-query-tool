# SQL 智能补全使用指南

## 功能概述

SQL 智能补全功能提供以下能力：

1. **SQL 关键字补全** - 自动提示 SELECT, FROM, WHERE 等关键字
2. **表名补全** - 根据数据库元数据提示表名
3. **列名补全** - 根据上下文提示列名
4. **上下文感知** - 在不同位置提供不同的建议

## 使用方法

### 基本使用

在 SQL 编辑器中输入时，补全会自动触发：

1. 输入 `SEL` → 提示 `SELECT`
2. 输入 `FROM us` → 提示 `users` 表
3. 输入 `WHERE id` → 提示 `id` 列

### 快捷键

- `Ctrl + Space` - 强制触发补全
- `Enter` / `Tab` - 确认选择
- `Esc` - 关闭补全窗口
- `↑` / `↓` - 选择建议项

### 配置

#### 自定义关键字

编辑 `resources/data/sql_keywords.json`：

```json
{
  "CUSTOM": ["MY_KEYWORD", "MY_FUNCTION"]
}
```

#### 调整触发延迟

在代码中修改：

```python
completer.setCompletionMode(QCompleter.PopupCompletion)
```

## 工作原理

### 架构

```
SQLQueryDialog
├── SQLCompleter
│   ├── SQLKeywordProvider (关键字)
│   └── LocalMetadataCache (元数据缓存)
├── MetadataSyncService (同步服务)
└── DataService (数据服务)
```

### 数据流

1. 打开 SQL 对话框 → 启动元数据同步
2. 同步服务从数据库读取表结构
3. 表结构存储到本地 SQLite 缓存
4. 用户输入时 → 查询缓存获取建议
5. 每 5 分钟自动刷新元数据

## 故障排除

### 补全不工作

1. 检查元数据是否已同步
2. 查看日志文件 `log/app.log`
3. 手动触发同步：刷新按钮

### 表名不显示

1. 确认数据库连接正常
2. 检查表权限
3. 查看元数据缓存文件 `data/metadata_cache.db`

## API 参考

参见 `docs/api/sql_completer_api.md`
