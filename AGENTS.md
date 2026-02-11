# AGENTS.md - 项目开发规范

本项目是一个基于 PySide2 的桌面应用程序，使用分层架构（表示层、业务逻辑层、数据访问层、基础设施层）。

## 构建/测试/检查命令

```bash
# 运行所有测试
python -m unittest discover tests/unit

# 运行单个测试文件
python -m unittest tests.unit.test_security_utils

# 运行单个测试类
python -m unittest tests.unit.test_security_utils.TestSecurityUtils

# 运行单个测试方法
python -m unittest tests.unit.test_security_utils.TestSecurityUtils.test_encrypt_password

# 使用 pytest 运行测试
pytest tests/unit -v

# 代码风格检查
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 代码格式化检查
black --check .

# 自动格式化代码
black .

# 导入语句排序检查
isort --check-only .

# 自动排序导入
isort .

# 本地构建
python build.py

# 安装依赖
pip install -r requirements.txt

# 启动应用程序
python src/main.py

# 或使用 desktop_app.py
python desktop_app.py
```

## 代码风格规范

### 文件头格式

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模块功能描述

详细描述模块的功能和用途
"""
```

### 导入语句顺序

1. 标准库导入
2. 第三方库导入
3. 本地模块导入

```python
import sys
import os
from typing import Dict, List, Optional, Union

from PySide2.QtWidgets import QApplication, QMainWindow
from PySide2.QtCore import Qt

from src.infrastructure.config.config_manager import get_config_manager
```

### 命名规范

- **类名**: 使用 `PascalCase`，如 `MainWindow`、`SecurityUtils`
- **函数/方法名**: 使用 `snake_case`，如 `get_config_manager`、`encrypt_password`
- **常量**: 使用 `UPPER_SNAKE_CASE`
- **私有成员**: 使用单下划线前缀，如 `_load_config`
- **保护成员**: 使用单下划线前缀

### 类型注解

- 函数参数和返回值应使用类型注解
- 使用 `typing` 模块中的类型，如 `Dict[str, Any]`、`Optional[str]`

```python
def get(self, key: str, default: Any = None) -> Any:
    """获取配置值"""
    pass
```

### 文档字符串

- 使用三重双引号 `"""`
- 类和公共方法必须包含文档字符串
- 函数文档字符串格式：

```python
def example_function(param1: str, param2: int) -> bool:
    """
    函数简短描述

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        bool: 返回值的描述
    """
    pass
```

### 错误处理

- 使用 try-except 捕获特定异常
- 记录错误日志时使用 `logger.error(msg, exc_info=True)`
- 用户操作错误应显示友好的 QMessageBox 提示

```python
try:
    result = some_operation()
except FileNotFoundError as e:
    logger.error(f"文件不存在: {str(e)}", exc_info=True)
    QMessageBox.critical(self, "错误", f"文件不存在: {str(e)}")
except Exception as e:
    logger.error(f"操作失败: {str(e)}", exc_info=True)
    QMessageBox.critical(self, "错误", f"操作失败: {str(e)}")
```

### 日志记录

- 使用 `logging.getLogger(__name__)` 获取日志记录器
- 日志级别：DEBUG（调试信息）、INFO（一般信息）、WARNING（警告）、ERROR（错误）

```python
import logging

logger = logging.getLogger(__name__)

logger.info("应用程序启动")
logger.error(f"发生错误: {str(e)}", exc_info=True)
```

### 类定义规范

- 类之间使用两个空行分隔
- 方法之间使用一个空行
- 类文档字符串后紧跟方法定义

```python
class ConfigManager:
    """
    配置管理器类
    """

    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件（私有方法）"""
        pass
```

### 代码格式化

- 使用 black 进行代码格式化（行长度限制 88 字符）
- 使用 isort 进行导入排序
- 使用 flake8 进行代码风格检查

## 项目结构

```
src/
├── presentation/          # 表示层（UI相关）
│   ├── windows/           # 主窗口
│   ├── dialogs/           # 对话框
│   └── widgets/           # 自定义控件
├── business/              # 业务逻辑层
│   ├── services/          # 服务类
│   └── models/            # 业务模型
├── data/                  # 数据访问层
│   ├── repositories/      # 数据仓库
│   └── entities/          # 数据实体
├── infrastructure/        # 基础设施层
│   ├── config/            # 配置管理
│   ├── security/          # 安全工具
│   └── logging/           # 日志管理
└── main.py                # 主入口
tests/
├── unit/                  # 单元测试
└── integration/           # 集成测试
```

## Qt 相关规范

- 使用 PySide2 而不是 PyQt5
- 信号槽连接使用 `clicked.connect()` 方式
- 子类化 Qt 类时，调用 `super().__init__()`
- 布局设置边距：`layout.setContentsMargins(10, 10, 10, 10)`

## 配置文件

- 使用 JSON 格式的 `config.json`
- 配置项使用点号分隔的嵌套键，如 `database.server`
- 敏感信息（密码）应加密存储

## Git 提交规范

- 提交信息使用中文
- 格式：`<类型>: <描述>`
- 类型：feat(新功能)、fix(修复)、docs(文档)、style(格式)、refactor(重构)、test(测试)
