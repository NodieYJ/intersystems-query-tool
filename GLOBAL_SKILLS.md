# 全局 Skills 配置汇总

## 📁 全局 Skills 路径

所有 skills 已配置为**全局级别**，可在任意项目中使用。

### 1. Oh-My-OpenCode Skills
**路径**: `~/.claude/skills/`

| Skill 名称 | 状态 | 描述 |
|-----------|------|------|
| git-master | ✅ 全局 | Git 版本控制专家 |
| playwright | ✅ 全局 | 浏览器自动化测试 |
| frontend-ui-ux | ✅ 全局 | 前端 UI/UX 设计 |
| python-expert | ✅ 全局 | Python 开发专家 |
| pyside2-expert | ✅ 全局 | PySide2/Qt 专家 |
| database-expert | ✅ 全局 | 数据库专家 |

**使用方式**: 通过 oh-my-opencode 的 `task` 工具
```typescript
task(
  category="deep",
  load_skills=["python-expert", "pyside2-expert"],
  prompt="优化代码"
)
```

---

### 2. OpenCode Native Skills
**路径**: `~/.config/opencode/skill/`

| Skill 名称 | 状态 | 描述 |
|-----------|------|------|
| hello-world | ✅ 全局 | 示例 Skill |
| code-review | ✅ 全局 | 代码审查指南 |
| project-guide | ✅ 全局 | 项目开发规范 |

**使用方式**: 通过 OpenCode 的 `skill` 工具
```
使用 code-review skill 审查代码
```

---

## 📊 汇总统计

| 类型 | 数量 | 全局路径 |
|------|------|----------|
| Oh-My-OpenCode | 6个 | `~/.claude/skills/` |
| OpenCode Native | 3个 | `~/.config/opencode/skill/` |
| **合计** | **9个** | - |

---

## 🔧 快速命令

```bash
# 查看所有全局 oh-my-opencode skills
ls ~/.claude/skills/

# 查看所有全局 OpenCode native skills
ls ~/.config/opencode/skill/

# 查看特定 skill 内容
cat ~/.claude/skills/git-master/SKILL.md
cat ~/.config/opencode/skill/code-review/SKILL.md
```

---

## 📂 项目级 Skills（已保留）

项目目录下仍保留原始 skills，作为备份和版本控制：

```
D:\pywindows
├── .opencode/skills/     # oh-my-opencode skills (项目级备份)
├── skill/                # OpenCode native skills (项目级备份)
```

---

## ✅ 配置完成时间
2026-02-12

所有 skills 现在可以在**任意项目**中使用！
