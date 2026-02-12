# 项目系统要求和环境配置规范

**文档版本**: 1.0  
**创建日期**: 2026-02-12  
**适用项目**: InterSystems数据库查询分析工具  

---

## 1. 操作系统要求

### 1.1 主要支持平台

| 操作系统 | 版本 | 支持状态 | 备注 |
|---------|------|---------|------|
| **Windows 7** | SP1 + 更新 | ✅ 主要目标 | 企业客户主要环境 |
| Windows 10 | 1809+ | ✅ 支持 | 推荐用于开发 |
| Windows 11 | 21H2+ | ✅ 支持 | 可选 |
| Windows Server | 2016+ | ⚠️ 有限支持 | 仅测试 |

### 1.2 Windows 7 特殊要求

- **Service Pack**: SP1 (必须)
- **更新**: 安装所有重要更新
- **.NET Framework**: 4.5 或更高版本
- **Visual C++ Redistributable**: 2015-2019
- **TLS/SSL**: 可能需要启用 TLS 1.2

---

## 2. Python 版本要求

### 2.1 目标 Python 版本

| 场景 | Python 版本 | 状态 | 说明 |
|------|-------------|------|------|
| **生产环境 (Win7)** | **3.8.10** | ✅ 强制 | Windows 7 支持的最后一个版本 |
| 生产环境 (Win10+) | 3.9.x | ⚠️ 可选 | 需要客户确认 |
| 开发环境 | 3.8.10 | ✅ 推荐 | 与生产环境保持一致 |
| CI/CD | 3.8.10 | ✅ 必须 | 确保测试一致性 |

### 2.2 Python 版本限制原因

**Windows 7 支持截止**: Python 3.8.10  
- Python 3.9 及更高版本不再支持 Windows 7
- Python 3.8.10 是 Windows 7 上可运行的最高版本

### 2.3 Python 安装要求

```
下载地址: https://www.python.org/downloads/release/python-3810/
安装包: python-3.8.10.exe (64位推荐)
```

**安装选项**:
- ✅ Add Python 3.8 to PATH
- ✅ Install pip
- ✅ Install for all users (推荐)

---

## 3. 核心依赖版本规范

### 3.1 必须依赖 (requirements.txt)

| 包名 | 当前版本 | Python 3.8 最高版本 | 版本限制原因 |
|------|---------|-------------------|-------------|
| **PySide2** | 5.14.0 | 5.15.2 | Qt GUI框架，需与Python版本匹配 |
| **shiboken2** | 5.14.0 | 5.15.2 | PySide2依赖的绑定生成器 |
| **pandas** | >=1.3.0,<2.0 | 1.5.3 | 数据处理，<2.0兼容性更好 |
| **numpy** | >=1.20.0,<1.24 | 1.24.4 | 数值计算，pandas依赖 |
| **cryptography** | >=3.4.8 | 42.0.x | 密码加密，安全依赖 |
| **setuptools** | 56.0.0 | 75.0+ | 包管理 |

### 3.2 可选依赖

| 包名 | 版本要求 | 用途 | 说明 |
|------|---------|------|------|
| **pyqtgraph** | >=0.12.0 | 图表绘制 | 数据分析可视化 |
| **openpyxl** | >=3.0.0 | Excel导出 | 数据导出功能 |

### 3.3 数据库驱动 (按需安装)

| 数据库 | 驱动包 | 版本 | 说明 |
|--------|--------|------|------|
| Intersystems IRIS | intersystems-irispython | 最新 | 主要数据库 |
| MySQL | pymysql | >=1.0 | 可选支持 |
| PostgreSQL | psycopg2 | >=2.9 | 可选支持 |
| SQL Server | pyodbc | >=4.0 | 可选支持 |
| Oracle | cx_Oracle | >=8.0 | 可选支持 |

### 3.4 开发依赖

| 包名 | 版本要求 | 用途 | Python 3.8 最高版本 |
|------|---------|------|-------------------|
| **pytest** | >=6.0 | 测试框架 | 8.3.x |
| **pytest-cov** | >=2.12 | 覆盖率 | 6.0.x |
| **flake8** | >=4.0 | 代码检查 | 7.0+ |
| **black** | >=21.0 | 代码格式化 | 24.8.x |
| **isort** | >=5.0 | 导入排序 | 5.13.x |

---

## 4. 代码兼容性规范

### 4.1 Python 3.8 语法限制

| 特性 | Python 3.8 | Python 3.9+ | 项目使用规则 |
|------|------------|-------------|-------------|
| `list[int]` | ❌ 不支持 | ✅ 支持 | 使用 `List[int]` |
| `dict[str, int]` | ❌ 不支持 | ✅ 支持 | 使用 `Dict[str, int]` |
| `tuple[int, int]` | ❌ 不支持 | ✅ 支持 | 使用 `Tuple[int, int]` |
| `set[int]` | ❌ 不支持 | ✅ 支持 | 使用 `Set[int]` |
| `X \| Y` (联合类型) | ❌ 不支持 | ✅ 3.10+ | 使用 `Union[X, Y]` |
| `str | None` | ❌ 不支持 | ✅ 3.10+ | 使用 `Optional[str]` |
| 海象运算符 `:=` | ✅ 支持 | ✅ 支持 | 可以使用 |
| f-string `=` | ✅ 支持 | ✅ 支持 | 可以使用 |

### 4.2 类型注解规范

**正确示例 (Python 3.8 兼容)**:
```python
from typing import List, Dict, Tuple, Set, Optional, Union

# 列表
items: List[str] = []

# 字典
config: Dict[str, int] = {}

# 元组
point: Tuple[int, int] = (0, 0)

# 可选类型
name: Optional[str] = None

# 联合类型
result: Union[str, int] = "ok"
```

**错误示例 (Python 3.9+ 语法)**:
```python
# 不要这样写！
items: list[str] = []           # ❌ Python 3.8 不支持
config: dict[str, int] = {}     # ❌ Python 3.8 不支持
point: tuple[int, int] = (0, 0) # ❌ Python 3.8 不支持
name: str | None = None         # ❌ Python 3.10+ 语法
```

### 4.3 导入规范

```python
# 标准库
import sys
import os
from typing import List, Dict, Tuple, Optional, Union, Any

# 第三方库
from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import Qt, Signal
import pandas as pd
import numpy as np

# 本地模块
from src.infrastructure.config.config_manager import get_config_manager
from src.business.services.data_service import DataService
```

---

## 5. 配置文件规范

### 5.1 setup.py 配置

```python
setup(
    python_requires=">=3.8,<3.9",  # 明确限制Python版本
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'Operating System :: Microsoft :: Windows',
    ],
    # ...
)
```

### 5.2 pyproject.toml 配置

```toml
[project]
requires-python = ">=3.8,<3.9"

[tool.black]
target-version = ['py38']  # Black格式化目标Python版本
```

### 5.3 requirements.txt 格式

```txt
# 核心依赖（固定版本）
PySide2==5.14.0
shiboken2==5.14.0
setuptools==56.0.0

# 安全依赖
cryptography>=3.4.8

# 数据处理（版本范围）
pandas>=1.3.0,<2.0
numpy>=1.20.0,<1.24

# 可选依赖（条件安装）
pyqtgraph>=0.12.0; python_version >= "3.8"
openpyxl>=3.0.0; python_version >= "3.8"

# 测试依赖
pytest>=6.0
pytest-cov>=2.12

# 代码质量
flake8>=4.0
black>=21.0
isort>=5.0
```

---

## 6. 环境验证脚本

### 6.1 Python 版本检查

```python
#!/usr/bin/env python3
"""验证Python版本是否符合要求"""
import sys

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 8
REQUIRED_MICRO = 10

version_info = sys.version_info

if version_info.major != REQUIRED_MAJOR:
    print(f"错误: 需要 Python {REQUIRED_MAJOR}.x，当前是 {version_info.major}.x")
    sys.exit(1)

if version_info.minor != REQUIRED_MINOR:
    print(f"错误: 需要 Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}.x，当前是 {version_info.major}.{version_info.minor}.x")
    sys.exit(1)

if version_info.micro > REQUIRED_MICRO:
    print(f"警告: 建议使用 Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}.{REQUIRED_MICRO}，当前是 {version_info.major}.{version_info.minor}.{version_info.micro}")
else:
    print(f"✓ Python 版本正确: {version_info.major}.{version_info.minor}.{version_info.micro}")

sys.exit(0)
```

### 6.2 依赖版本检查

```python
#!/usr/bin/env python3
"""验证关键依赖版本"""
import sys

def check_package(package_name, min_version, max_version=None):
    try:
        module = __import__(package_name)
        version = module.__version__
        
        # 版本比较逻辑...
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError:
        print(f"✗ {package_name}: 未安装")
        return False

# 检查核心依赖
check_package("PySide2", "5.14.0", "5.15.2")
check_package("pandas", "1.3.0", "1.5.3")
check_package("numpy", "1.20.0", "1.24.4")
```

---

## 7. 部署检查清单

### 7.1 部署前检查

- [ ] Python 版本为 3.8.10
- [ ] 操作系统为 Windows 7 SP1 或更高
- [ ] 安装 .NET Framework 4.5+
- [ ] 安装 Visual C++ Redistributable 2015-2019
- [ ] 网络连接正常（用于首次运行检查更新）

### 7.2 安装后验证

- [ ] 运行 `python --version` 显示 3.8.10
- [ ] 运行 `pip list` 确认所有依赖已安装
- [ ] 运行 `python -c "import PySide2; print(PySide2.__version__)"` 确认 PySide2
- [ ] 运行单元测试全部通过
- [ ] 启动应用程序无错误

---

## 8. 更新和升级策略

### 8.1 Python 版本升级路径

当需要支持更高 Python 版本时：

| 当前 | 目标 | 工作量 | 风险 |
|------|------|--------|------|
| Python 3.8 | Python 3.9 | 小 | 低 |
| Python 3.8 | Python 3.10 | 中 | 中 |
| Python 3.8 | Python 3.11+ | 大 | 高 |

### 8.2 依赖升级原则

1. **PySide2**: 保持 5.14.0-5.15.x 范围内
2. **pandas**: 不超过 1.5.3（Python 3.8 限制）
3. **numpy**: 不超过 1.24.4（Python 3.8 限制）
4. **其他**: 在兼容范围内使用最新版本

### 8.3 版本升级检查流程

1. 在虚拟环境中测试新版本
2. 运行完整测试套件
3. 在 Windows 7 环境验证
4. 检查 PySide2 兼容性
5. 更新文档和配置文件
6. 发布前进行 Beta 测试

---

## 9. 故障排除

### 9.1 常见问题

**Q: PySide2 安装失败**
```
解决方案:
1. 确认 Python 版本 <= 3.9
2. 升级 pip: python -m pip install --upgrade pip
3. 安装 Visual C++ Redistributable
4. 使用 wheel 安装: pip install PySide2==5.14.0
```

**Q: pandas 导入错误**
```
解决方案:
1. 确认 numpy 版本兼容: pip install numpy==1.23.5
2. 重新安装 pandas: pip install pandas==1.3.5
3. 检查依赖冲突: pip check
```

**Q: Windows 7 上 Python 3.8 无法安装**
```
解决方案:
1. 安装 Windows 7 SP1
2. 安装所有重要更新
3. 安装 Universal C Runtime
4. 使用 32位 Python 3.8.10 (如果64位失败)
```

---

## 10. 文档维护

### 10.1 更新记录

| 日期 | 版本 | 更新内容 | 更新人 |
|------|------|---------|--------|
| 2026-02-12 | 1.0 | 初始版本 | AI Assistant |

### 10.2 审核周期

- 每季度检查依赖版本更新
- 每年评估 Python 版本升级需求
- 每次重大更新后更新本文档

---

**文档结束**

如有任何疑问，请参考 `environment/diffenvironment.md` 获取详细的兼容性分析报告。
