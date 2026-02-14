# UI 一致性重构计划

**计划日期**: 2026-02-15  
**项目**: PyWindows 桌面应用程序

---

## 1. 问题概述

UI 一致性审查发现以下问题：

| 问题 | 严重程度 | 影响范围 |
|------|----------|----------|
| COLORS 重复定义 | 🟡 中 | 5个文件 |
| 内联样式混用 | 🟡 中 | 4个对话框 |
| 间距定义不一致 | 🟢 低 | 2处定义 |
| 硬编码字体大小 | 🟢 低 | 若干处 |
| 工厂未被充分使用 | 🟢 低 | 部分代码 |

---

## 2. 重构方案

### 方案 A：渐进式重构（推荐）

**策略**：逐步迁移，每次只重构一个模块，保持功能正常。

**优点**：
- 风险低，每次改动小
- 易于测试和验证
- 不影响现有功能

**缺点**：
- 周期较长
- 需要多次提交

### 方案 B：一次性重构

**策略**：一次性修改所有文件，统一使用常量。

**优点**：
- 快速完成
- 一次性解决问题

**缺点**：
- 风险高
- 难以全面测试
- 可能引入回归问题

---

## 3. 详细实施计划

### 阶段 1：统一颜色系统（优先级：高）

**目标**：消除 COLORS 重复定义，统一从 ui_constants.py 导入。

**修改文件**：
1. `main_window.py` - 删除重复的 COLORS 定义，添加导入
2. `main_window_ui.py` - 删除重复的 COLORS 定义，添加导入
3. `main_window_pages.py` - 删除重复的 COLORS 定义，添加导入
4. `main_window_components.py` - 删除重复的 COLORS 定义，添加导入

**代码变更**：
```python
# 修改前
COLORS = {
    'primary': '#2563EB',
    ...
}

# 修改后
from src.presentation.windows.ui_constants import COLORS
```

**预计改动量**：删除 ~80 行，新增 4 行导入

---

### 阶段 2：统一间距系统（优先级：中）

**目标**：统一使用 ui_constants.py 的 SPACING。

**修改文件**：
1. `constants.py` - 移除 LAYOUT_SPACING，改为引用 ui_constants
2. 所有使用硬编码间距的对话框

**代码变更**：
```python
# 修改前
layout.setContentsMargins(10, 10, 10, 10)

# 修改后
from src.presentation.windows.ui_constants import SPACING
layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
```

---

### 阶段 3：消除内联样式（优先级：中）

**目标**：将内联样式迁移到 QSS 文件或使用 ObjectName。

**修改文件**：
1. `sql_query_dialog.py` - 移除内联表格样式，添加到 app.qss
2. `query_history_dialog.py` - 统一使用 ObjectName
3. `connection_config_dialog.py` - 使用 COLORS 常量

**示例**：
```python
# 修改前
self.db_path_label.setStyleSheet("color: green;")

# 修改后
self.db_path_label.setObjectName('status_success')
# 在 app.qss 中添加
QLabel#status_success {
    color: #10B981;
}
```

---

### 阶段 4：推广组件工厂（优先级：低）

**目标**：鼓励使用 UIButtonFactory 创建按钮。

**修改文件**：
- 所有直接创建按钮的代码

**示例**：
```python
# 修改前
btn = QPushButton("Text", self)
btn.setObjectName('btn_primary')

# 修改后
from src.presentation.utils.ui_factories import UIButtonFactory
btn = UIButtonFactory.create_primary_button("Text", self)
```

---

## 4. 实施顺序

```
阶段 1 (高优先级)
    ↓
阶段 2 (中优先级)
    ↓
阶段 3 (中优先级)
    ↓
阶段 4 (低优先级)
```

---

## 5. 风险评估

| 阶段 | 风险等级 | 缓解措施 |
|------|----------|----------|
| 阶段 1 | 🟡 中 | 每次只修改一个文件，运行测试 |
| 阶段 2 | 🟡 中 | 使用 IDE 重构功能 |
| 阶段 3 | 🟡 中 | 保留内联样式作为 fallback |
| 阶段 4 | 🟢 低 | 保持向后兼容 |

---

## 6. 验收标准

- [ ] COLORS 只在 ui_constants.py 中定义
- [ ] 所有间距使用 SPACING 常量
- [ ] 内联样式减少 80%
- [ ] 单元测试全部通过
- [ ] UI 行为无变化

---

## 7. 预计工作量

| 阶段 | 预计时间 | 改动文件数 |
|------|----------|------------|
| 阶段 1 | 30 分钟 | 4 |
| 阶段 2 | 45 分钟 | 6 |
| 阶段 3 | 60 分钟 | 4 |
| 阶段 4 | 30 分钟 | 若干 |

**总计**: ~3 小时

---

**计划制定完成**

是否需要开始执行此计划？
