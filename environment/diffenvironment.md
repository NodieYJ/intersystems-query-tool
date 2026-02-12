# Python 3.8.10 兼容性检查报告

**检查日期**: 2026-02-12  
**目标Python版本**: 3.8.10 (Windows 7支持的最后一个Python版本)  
**当前Python版本**: 3.14.3  
**项目**: InterSystems数据库查询分析工具

---

## 1. 概述

本报告基于 **Python 3.8.10** 检查项目代码和依赖的兼容性。Windows 7 官方支持的最后一个 Python 版本是 3.8.10。

---

## 2. 代码不兼容问题

### 2.1 内置泛型类型注解 (Python 3.9+)

**问题描述**: 使用了 Python 3.9+ 引入的内置泛型类型（如 `tuple[int, int]`），这在 Python 3.8 中需要使用 `typing` 模块。

**受影响文件**:

| 文件路径 | 行号 | 问题代码 | 修复建议 |
|---------|------|----------|----------|
| `src/infrastructure/utils/scaling_manager.py` | 67 | `self._screen_resolution: tuple[int, int] = (1920, 1080)` | `self._screen_resolution: Tuple[int, int] = (1920, 1080)` |

**Python 3.8 兼容写法**:
```python
from typing import Tuple

# 修复前 (Python 3.9+)
self._screen_resolution: tuple[int, int] = (1920, 1080)

# 修复后 (Python 3.8)
self._screen_resolution: Tuple[int, int] = (1920, 1080)
```

### 2.2 类型注解最佳实践

**建议检查项**:

| 特性 | Python 3.8 | Python 3.9+ | 状态 |
|------|------------|-------------|------|
| `list[int]` | 不支持 | 支持 | ✅ 项目未使用 |
| `dict[str, int]` | 不支持 | 支持 | ✅ 项目未使用 |
| `tuple[int, ...]` | 不支持 | 支持 | ⚠️ scaling_manager.py:67使用 |
| `X \| Y` (联合类型) | 不支持 | 3.10+ | ✅ 项目未使用 |

---

## 3. 依赖版本兼容性

### 3.1 主要依赖

| 依赖包 | 当前版本 | Python 3.8兼容版本 | Python 3.8最高版本 | 状态 |
|--------|----------|-------------------|-------------------|------|
| **PySide2** | 5.14.0 | 5.11-5.15 | 5.15.2 | ✅ 兼容 |
| **shiboken2** | 5.14.0 | 5.11-5.15 | 5.15.2 | ✅ 兼容 |
| **pandas** | >=1.3.0,<2.0 | 1.3.x-1.5.x | 1.5.3 | ✅ 兼容 |
| **numpy** | >=1.20.0,<1.24 | 1.20.x-1.24.x | 1.24.4 | ✅ 兼容 |
| **cryptography** | >=3.4.8 | 3.4.8+ | 42.0.x | ✅ 兼容 |
| **setuptools** | 56.0.0 | 45.0+ | 75.0+ | ✅ 兼容 |

### 3.2 开发依赖

| 依赖包 | 当前版本 | Python 3.8兼容版本 | Python 3.8最高版本 | 状态 |
|--------|----------|-------------------|-------------------|------|
| **pytest** | >=6.0 | 6.0+ | 8.3.x | ✅ 兼容 |
| **pytest-cov** | >=2.12 | 2.12+ | 6.0.x | ✅ 兼容 |
| **flake8** | >=4.0 | 4.0+ | 7.0+ | ✅ 兼容 |
| **black** | >=21.0 | 21.0+ | 24.8.x | ✅ 兼容 |
| **isort** | >=5.0 | 5.0+ | 5.13.x | ✅ 兼容 |

### 3.3 可选依赖

| 依赖包 | 当前版本 | Python 3.8兼容版本 | 状态 |
|--------|----------|-------------------|------|
| **pyqtgraph** | >=0.12.0 | 0.12+ | ✅ 兼容 |
| **openpyxl** | >=3.0.0 | 3.0+ | ✅ 兼容 |

### 3.4 当前环境不兼容警告

**⚠️ 当前系统环境 (Python 3.14.3) 无法安装 PySide2 5.14.0**

PySide2 5.14.0 支持的 Python 版本范围：3.5 - 3.9

**解决方案**:
1. 安装 Python 3.8.10 (Windows 7)
2. 然后执行: `pip install -r requirements.txt`

---

## 4. Python 3.8 新特性使用检查

### 4.1 海象运算符 (:=) - Python 3.8+

**检查结果**: ✅ 项目未使用

海象运算符在 Python 3.8 中引入，如果需要支持 Python 3.7 才需要避免使用。

### 4.2 位置参数限制 (/)

**检查结果**: ✅ 项目未使用

### 4.3 f-string 增强 (f"{expr=}")

**检查结果**: ✅ 项目未使用

---

## 5. 修复建议

### 5.1 立即修复

**文件**: `src/infrastructure/utils/scaling_manager.py`

**修改前**:
```python
import logging
import threading
from typing import Optional

class ScalingManager:
    def __init__(self):
        self._screen_resolution: tuple[int, int] = (1920, 1080)  # 第67行
```

**修改后**:
```python
import logging
import threading
from typing import Optional, Tuple  # 添加 Tuple 导入

class ScalingManager:
    def __init__(self):
        self._screen_resolution: Tuple[int, int] = (1920, 1080)  # 使用 Tuple
```

### 5.2 预防措施

建议在 `setup.cfg` 或 `pyproject.toml` 中添加 Python 版本限制：

```toml
# pyproject.toml
[project]
requires-python = ">=3.8,<3.9"
```

或在 `setup.py` 中添加：

```python
setup(
    python_requires=">=3.8,<3.9",
    ...
)
```

---

## 6. Windows 7 部署建议

### 6.1 环境准备

1. **下载 Python 3.8.10**:
   - 官网: https://www.python.org/downloads/release/python-3810/
   - 下载: `python-3.8.10.exe`

2. **安装选项**:
   - 勾选 "Add Python to PATH"
   - 选择 "Customize installation"
   - 确保选中 "pip" 和 "Add to environment variables"

3. **验证安装**:
   ```cmd
   python --version
   # 应显示: Python 3.8.10
   ```

### 6.2 依赖安装

```cmd
# 升级 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证 PySide2 安装
python -c "import PySide2; print(PySide2.__version__)"
```

### 6.3 已知限制

| 项目 | Windows 7 限制 |
|------|---------------|
| Python 版本 | 最高 3.8.10 |
| PySide2 版本 | 最高 5.15.2 |
| TLS/SSL | 可能需要更新 |
| .NET Framework | 可能需要 4.5+ |

---

## 7. 总结

### 7.1 兼容性状态

| 类别 | 状态 | 备注 |
|------|------|------|
| **代码兼容性** | ⚠️ 1处需修复 | `tuple[int, int]` → `Tuple[int, int]` |
| **依赖兼容性** | ✅ 全部兼容 | 所有依赖支持 Python 3.8 |
| **测试兼容性** | ✅ 兼容 | 测试框架支持 Python 3.8 |
| **部署可行性** | ✅ 可行 | 需要 Python 3.8.10 环境 |

### 7.2 工作量评估

| 任务 | 工作量 | 优先级 |
|------|--------|--------|
| 修复类型注解 | 5分钟 | P0 |
| 添加 Python 版本限制 | 5分钟 | P1 |
| Windows 7 环境搭建 | 30分钟 | P0 |
| 完整测试验证 | 2小时 | P1 |

### 7.3 下一步行动

1. **立即修复**: 修改 `scaling_manager.py` 第67行
2. **配置锁定**: 添加 `python_requires` 限制
3. **环境搭建**: 在 Windows 7 安装 Python 3.8.10
4. **测试验证**: 在 Windows 7 环境运行完整测试

---

**报告生成时间**: 2026-02-12  
**报告版本**: 1.0  
**下次更新**: 修复完成后
