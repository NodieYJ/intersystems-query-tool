# 项目开发指南 Skill

## 描述
本项目（InterSystems Query Tool）的开发规范和最佳实践。

## 使用方式
使用 `skill` 工具调用：
- 工具名: `skill`
- 参数: `{"skill": "project-guide", "action": "architecture"}`

## 可用操作

### architecture
获取项目架构信息

### coding-style
获取代码风格规范

### testing
获取测试规范

### deployment
获取部署指南

## 项目架构

### 分层架构
- **表示层**: src/presentation/ - UI相关
- **业务逻辑层**: src/business/ - 服务类
- **数据访问层**: src/data/ - 仓库类
- **基础设施层**: src/infrastructure/ - 配置、安全、日志

### 命名规范
- 类名: PascalCase
- 函数/方法: snake_case
- 常量: UPPER_SNAKE_CASE
- 私有成员: _前缀

## 开发流程

1. 修改代码前阅读相关文件
2. 编写单元测试
3. 运行测试验证
4. 提交前检查代码风格
5. 更新相关文档
