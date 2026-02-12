# OpenCode Skills 系统配置

## 配置状态

✅ **OpenCode 版本**: 1.1.59（支持原生 Skills）
✅ **Skills 系统**: 已启用
✅ **权限配置**: 已设置（允许所有 skills）

## 目录结构

```
~/.config/opencode/skill/          # 全局 Skills（所有项目可用）
├── code-review/SKILL.md           # 代码审查指南
└── hello-world/SKILL.md           # 示例 Skill

./skill/                           # 项目 Skills（当前项目可用）
└── project-guide/SKILL.md         # 项目开发指南
```

## 已安装的 Skills

### 全局 Skills

#### 1. hello-world
- **用途**: 示例 Skill，测试 Skills 系统
- **位置**: `~/.config/opencode/skill/hello-world/`
- **功能**: 返回问候语和当前时间

#### 2. code-review
- **用途**: 代码审查最佳实践
- **位置**: `~/.config/opencode/skill/code-review/`
- **功能**: 提供代码审查检查清单

### 项目 Skills

#### 3. project-guide
- **用途**: 本项目开发规范
- **位置**: `./skill/project-guide/`
- **功能**: 提供项目架构、代码风格、测试和部署指南

## 使用方法

### 在 OpenCode 中调用 Skill

Skills 通过 `skill` 工具调用，格式如下：

```json
{
  "skill": "skill-name",
  "action": "action-name",
  "param1": "value1"
}
```

### 示例调用

**调用 hello-world skill:**
```
请使用 hello-world skill 向我问候
```

**调用 code-review skill:**
```
请使用 code-review skill 获取 Python 代码审查检查清单
```

**调用 project-guide skill:**
```
请使用 project-guide skill 查看项目架构信息
```

## 配置详情

### 全局配置
文件: `~/.config/opencode/opencode.json`

```json
{
  "permission": {
    "skill": {
      "*": "allow"
    }
  }
}
```

### 权限说明
- `"*": "allow"` - 允许使用所有 skills
- 可以针对特定 skill 设置权限：
  ```json
  {
    "permission": {
      "skill": {
        "code-review": "allow",
        "hello-world": "deny",
        "*": "ask"
      }
    }
  }
  ```

## 创建新 Skill

### 步骤

1. 创建 skill 目录
   ```bash
   mkdir -p ~/.config/opencode/skill/my-skill
   ```

2. 创建 SKILL.md 文件
   ```bash
   cat > ~/.config/opencode/skill/my-skill/SKILL.md << 'EOF'
   # My Skill
   
   ## 描述
   Skill 的简要描述
   
   ## 使用方式
   如何使用此 skill
   
   ## 参数
   - param1: 参数1说明
   - param2: 参数2说明
   
   ## 示例
   使用示例
   EOF
   ```

3. 在 OpenCode 中使用
   ```
   请使用 my-skill 执行 xxx 操作
   ```

### Skill 文件格式

每个 skill 需要一个 `SKILL.md` 文件，包含：
- **标题**: Skill 名称
- **描述**: 简要说明用途
- **使用方式**: 调用方法和参数
- **功能列表**: 可用操作和返回值

## 注意事项

1. **懒加载**: Skills 是按需加载的，不会占用启动时间
2. **权限控制**: 可以通过 `permission.skill` 控制访问
3. **全局 vs 项目**: 
   - 全局 skills 放在 `~/.config/opencode/skill/`
   - 项目 skills 放在项目根目录的 `skill/`
4. **命名规范**: skill 名称使用 kebab-case（短横线连接）

## 故障排除

### Skill 无法加载
1. 检查 SKILL.md 文件是否存在
2. 检查权限配置是否正确
3. 检查 OpenCode 版本 >= 1.0.190

### Permission Denied
1. 检查 `~/.config/opencode/opencode.json` 中的 permission 配置
2. 确保 `"skill": {"*": "allow"}` 或特定 skill 被允许

---

**配置完成时间**: 2026-02-12
**状态**: ✅ 运行正常
