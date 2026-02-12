# Skills 统一管理方案

## 📁 统一访问路径

所有全局 skills 现在可以通过统一路径访问：

```
C:\Users\Administrator\.config\skills\
├── oh-my-opencode\      → 链接到 ~/.claude/skills/
│   ├── git-master\
│   ├── playwright\
│   ├── frontend-ui-ux\
│   ├── python-expert\
│   ├── pyside2-expert\
│   ├── database-expert\
│   └── README.md
│
└── opencode-native\      → 链接到 ~/.config/opencode/skill/
    ├── hello-world\
    ├── code-review\
    └── project-guide\
```

## 🔗 物理路径映射

| 统一访问路径 | 实际物理路径 | 类型 |
|-------------|-------------|------|
| `~/.config/skills/oh-my-opencode/` | `~/.claude/skills/` | 符号链接 |
| `~/.config/skills/opencode-native/` | `~/.config/opencode/skill/` | 符号链接 |

## ⚠️ 为什么不建议混合存放

虽然可以将 skills 放在同一目录，但**强烈不建议**这样做：

### 1. 格式不同

**Oh-My-OpenCode Skills** (Front Matter 格式):
```markdown
---
name: skill-name
description: Description
mcp:
  server-name:
    command: npx
    args: ["-y", "@mcp/package"]
---

# Skill Content
```

**OpenCode Native Skills** (简单格式):
```markdown
# Skill Name

Description...
```

### 2. 调用方式不同

| 类型 | 调用方式 | 配置位置 |
|------|---------|---------|
| Oh-My-OpenCode | `task(load_skills=["skill-name"])` | `~/.claude/skills/` |
| OpenCode Native | `skill` 工具 | `~/.config/opencode/skill/` |

### 3. 加载机制不同
- **Oh-My-OpenCode**: 通过 Sisyphus 代理的 `task` 工具动态加载
- **OpenCode Native**: 通过 OpenCode 内置的 `skill` 工具调用

## ✅ 推荐方案：统一管理 + 分离存储

### 方案一：符号链接（当前采用）

**优点**:
- 统一访问入口
- 保持各自系统的兼容性
- 不会破坏原有配置

**访问方式**:
```bash
# 统一管理入口
cd ~/.config/skills/

# 查看所有 oh-my-opencode skills
ls oh-my-opencode/

# 查看所有 OpenCode native skills
ls opencode-native/
```

### 方案二：环境变量（可选）

如果要统一使用一个路径，可以设置环境变量：

```bash
# .bashrc 或 .zshrc
export OMC_SKILLS_PATH="$HOME/.config/skills/oh-my-opencode"
export OPCODE_SKILLS_PATH="$HOME/.config/skills/opencode-native"
```

### 方案三：批量管理脚本（可选）

创建管理脚本 `~/.config/skills/manage.sh`:

```bash
#!/bin/bash
# Skills 管理脚本

SKILLS_ROOT="$HOME/.config/skills"

list() {
    echo "=== Oh-My-OpenCode Skills ==="
    ls "$SKILLS_ROOT/oh-my-opencode/"
    echo
    echo "=== OpenCode Native Skills ==="
    ls "$SKILLS_ROOT/opencode-native/"
}

edit() {
    type=$1
    skill=$2
    if [ "$type" = "omo" ]; then
        code "$SKILLS_ROOT/oh-my-opencode/$skill/SKILL.md"
    else
        code "$SKILLS_ROOT/opencode-native/$skill/SKILL.md"
    fi
}

case $1 in
    list) list ;;
    edit) edit $2 $3 ;;
    *) echo "Usage: $0 {list|edit <omo|native> <skill-name>}" ;;
esac
```

## 📊 当前配置状态

| 系统 | 物理路径 | 统一访问路径 | Skills 数量 |
|------|---------|-------------|------------|
| Oh-My-OpenCode | `~/.claude/skills/` | `~/.config/skills/oh-my-opencode/` | 6个 |
| OpenCode Native | `~/.config/opencode/skill/` | `~/.config/skills/opencode-native/` | 3个 |
| **合计** | - | `~/.config/skills/` | **9个** |

## 🔧 快速命令

```bash
# 进入统一管理目录
cd ~/.config/skills

# 列出所有 skills
find . -name "SKILL.md" -exec dirname {} \; | sort

# 编辑特定 skill
notepad ~/.config/skills/oh-my-opencode/git-master/SKILL.md
notepad ~/.config/skills/opencode-native/code-review/SKILL.md
```

## 💡 使用建议

1. **日常管理**: 使用统一路径 `~/.config/skills/` 查看和管理
2. **编辑修改**: 通过统一路径编辑，修改会同步到原位置
3. **新增 skill**: 仍需根据类型添加到对应原位置
4. **备份同步**: 统一路径方便整体备份

---

**配置时间**: 2026-02-12  
**方案**: 统一管理 + 分离存储（符号链接）
