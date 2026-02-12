# 测试文件归档目录

## 说明

此目录包含从项目根目录移出的临时测试文件。这些文件不再用于正式测试，但保留了历史记录。

## 文件列表

### 根目录临时测试

| 文件 | 说明 | 状态 |
|------|------|------|
| `test_connection_simple.py` | 简单的数据库连接测试 | 已归档 |
| `test_scale.py` | 缩放功能测试 | 已归档 |
| `test_auto_height.py` | 自动高度调整测试 | 已归档 |
| `test_free_form.py` | 自由表单测试 | 已归档 |

### 依赖pytest的测试

| 文件 | 说明 | 依赖 | 状态 |
|------|------|------|------|
| `test_phase2_components.py` | 阶段2组件测试（插件系统、Hook管理） | pytest | 已归档 |
| `test_phase3_components.py` | 阶段3组件测试（Strategy模式） | pytest | 已归档 |
| `test_interfaces.py` | 接口和异常体系测试 | pytest | 已归档 |
| `conftest.py` | pytest配置文件 | pytest | 已归档 |

## 与正式测试的区别

### 正式测试（tests/ 目录）
- 使用 `unittest` 框架
- 结构化、可维护
- 持续集成支持
- 覆盖核心业务逻辑

### 归档测试（此目录）
- 临时性、探索性
- 未使用测试框架
- 用于开发调试
- 功能已整合到正式测试

## 历史背景

这些测试文件是在开发过程中创建的临时测试：

1. **test_connection_simple.py**
   - 开发初期快速验证数据库连接
   - 功能已整合到 `tests/unit/test_driver_factory.py`

2. **test_scale.py**
   - 测试UI缩放功能
   - 功能已整合到 `tests/unit/test_scaling_manager.py`

3. **test_auto_height.py**
   - 测试表格行高自动调整
   - 功能已整合到主程序中

4. **test_free_form.py**
   - 自由表单布局测试
   - 与归档的表单设计器相关

## 使用建议

1. **不要运行**：这些测试可能已过时，运行可能报错
2. **仅供参考**：查看实现思路和历史演进
3. **代码复用**：如需类似功能，参考这些代码而不是直接复制

## 正式测试目录

项目正式的单元测试和集成测试位于：
- `tests/unit/` - 单元测试
- `tests/integration/` - 集成测试
- `tests/performance/` - 性能测试

---
最后更新：2026-02-12
