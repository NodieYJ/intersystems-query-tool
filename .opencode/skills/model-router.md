# Model Router Skill
# 根据任务类型自动切换最优模型

## 任务-模型映射规则

### 代码生成/审查任务 → nim-llama3-70b
关键词:
- "写代码", "生成代码", "实现功能"
- "重构", "优化代码"
- "Bug修复", "调试"
- "SQL", "查询", "数据库"
- "算法", "设计模式"

### 架构设计任务 → nim-llama3-70b
关键词:
- "架构", "设计", "模块拆分"
- "技术选型", "方案对比"
- "性能优化"
- "依赖注入", "分层"

### 中文内容/文档 → glm-4.7-free
关键词:
- "写文档", "README", "注释"
- "总结", "解释", "说明"
- "文案", "介绍"

### 快速问答/配置 → glm-4.7-free
关键词:
- "怎么配置", "如何使用"
- "查看", "检查", "验证"
- "简单问题"

## 使用方式

在任务开始前，Orchestrator 检测用户输入：
1. 匹配关键词
2. 调用 `opencode models use <model>`
3. 执行任务

## 命令参考

```bash
# 切换到代码专用模型
opencode models use nim-llama3-70b

# 切换到中文通用模型  
opencode models use glm-4.7-free

# 切换到快速模型
opencode models use nim-llama3-8b

# 查看当前模型
opencode models current

# 列出可用模型
opencode models list
```
