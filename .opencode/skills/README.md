# Oh-My-OpenCode Skills 配置

## 概述

本目录包含 oh-my-opencode 的自定义 Skills，用于增强 AI 代理的专业能力。

## 目录结构

```
.opencode/skills/
├── git-master/           # Git 专家
├── playwright/           # 浏览器自动化
├── frontend-ui-ux/       # 前端 UI/UX 设计
├── python-expert/        # Python 开发专家
├── pyside2-expert/       # PySide2/Qt 专家
└── database-expert/      # 数据库专家
```

## Skills 说明

### 1. git-master
**用途**: Git 版本控制专家
**功能**:
- 检测提交风格并保持一致
- 将变更拆分为原子提交
- 制定 rebase 策略
- 分支管理建议

**使用场景**:
```
使用 git-master skill 提交当前变更
```

### 2. playwright
**用途**: 浏览器自动化测试
**功能**:
- UI 测试和验证
- 网页截图对比
- 网页数据抓取
- E2E 测试编写

**使用场景**:
```
使用 playwright skill 测试登录页面
```

### 3. frontend-ui-ux
**用途**: 前端设计专家
**功能**:
- 配色方案和对比度检查
- 字体和排版建议
- 动画和过渡效果
- 响应式布局设计

**使用场景**:
```
使用 frontend-ui-ux skill 优化界面设计
```

### 4. python-expert
**用途**: Python 开发专家
**功能**:
- Python 最佳实践和惯用法
- 设计模式和架构建议
- 测试和调试技巧
- 性能优化建议

**使用场景**:
```
使用 python-expert skill 审查代码风格
```

### 5. pyside2-expert
**用途**: PySide2/Qt 桌面应用开发专家
**功能**:
- GUI 设计和实现
- Signal/Slot 机制
- 多线程处理
- Qt Stylesheets

**使用场景**:
```
使用 pyside2-expert skill 优化主窗口布局
```

### 6. database-expert
**用途**: 数据库开发专家
**功能**:
- SQL 查询优化
- 连接池管理
- 数据库架构设计
- 事务处理

**使用场景**:
```
使用 database-expert skill 优化查询性能
```

## 使用方法

在 oh-my-opencode 中，通过 `task` 工具的 `load_skills` 参数加载 skills：

```typescript
task(
  category="deep",
  load_skills=["python-expert", "pyside2-expert"],
  prompt="优化主窗口的数据绑定逻辑"
)
```

## Category 与 Skill 组合建议

| 任务类型 | Category | 推荐 Skills |
|---------|----------|-------------|
| 代码提交 | `quick` | `git-master` |
| UI 实现 | `visual-engineering` | `frontend-ui-ux`, `playwright` |
| Python 开发 | `deep` | `python-expert` |
| 桌面应用 | `deep` | `pyside2-expert`, `python-expert` |
| 数据库 | `deep` | `database-expert`, `python-expert` |
| 架构设计 | `ultrabrain` | (纯推理) |
| 文档编写 | `writing` | `python-expert` |

## 示例任务

### 示例 1: 提交代码
```
**TASK**: 提交当前的 bug 修复
**CATEGORY**: quick
**LOAD_SKILLS**: ["git-master"]
**MUST_DO**: 
- 遵循现有的提交信息风格
- 将逻辑相关的变更拆分为原子提交
```

### 示例 2: 优化 UI
```
**TASK**: 优化数据表格的列宽自适应
**CATEGORY**: visual-engineering
**LOAD_SKILLS**: ["pyside2-expert", "frontend-ui-ux"]
**CONTEXT**: src/presentation/widgets/data_displays.py
**MUST_DO**:
- 确保列宽根据内容自动调整
- 保持界面美观和可用性
```

### 示例 3: 数据库优化
```
**TASK**: 优化查询历史记录的加载速度
**CATEGORY**: deep
**LOAD_SKILLS**: ["database-expert", "python-expert"]
**CONTEXT**: src/business/services/query_history_manager.py
**MUST_DO**:
- 分析当前查询性能瓶颈
- 实现适当的索引策略
- 添加查询缓存机制
```

## Skill 文件格式

每个 skill 是一个包含 `SKILL.md` 文件的目录：

```markdown
---
name: skill-name
description: Skill description
mcp:  # Optional MCP configuration
  mcp-name:
    command: npx
    args: ["-y", "@mcp/package"]
---

# Skill Name

Skill content and guidelines...
```

## 添加新 Skill

1. 创建 skill 目录:
   ```bash
   mkdir .opencode/skills/my-skill
   ```

2. 创建 SKILL.md:
   ```bash
   cat > .opencode/skills/my-skill/SKILL.md << 'EOF'
   ---
   name: my-skill
   description: My skill description
   ---
   
   # My Skill
   
   Skill content...
   EOF
   ```

3. 在任务中使用:
   ```
   使用 my-skill skill 执行 xxx 任务
   ```

## 注意事项

1. **懒加载**: Skills 是按需加载的，不会占用启动时间
2. **组合使用**: 可以同时加载多个 skills
3. **项目级**: 这些 skills 只在当前项目可用
4. **全局 skills**: 可以放在 `~/.claude/skills/` 供所有项目使用

---

**配置时间**: 2026-02-12
**版本**: oh-my-opencode 3.5.2
