# Presentation Layer API 文档

## 概述

表示层（Presentation Layer）包含所有 GUI 相关的类和模块。

## 模块结构

```
src/presentation/
├── dialogs/              # 对话框组件
│   ├── connection_config_dialog.py
│   ├── data_analysis_dialog.py
│   ├── data_download_dialog.py
│   ├── data_download_config_dialog.py
│   ├── gui_utils.py        # 新增：GUI 通用工具
│   ├── log_dialog.py
│   ├── query_history_dialog.py
│   └── sql_query_dialog.py
├── windows/              # 主窗口组件
│   └── main_window.py
├── widgets/              # 自定义控件
└── __init__.py
```

## 主要类

### LogDialog

日志查看对话框，提供日志文件的查看、搜索和高亮功能。

```python
from src.presentation.dialogs.log_dialog import LogDialog

# 创建对话框
dialog = LogDialog(parent=self)
dialog.exec_()
```

#### 属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `log_dir` | str | 日志文件目录路径 |
| `all_matches` | List[int] | 所有搜索匹配位置 |
| `current_match_index` | int | 当前匹配索引 |

#### 方法

##### `__init__(self, parent: Optional[QWidget] = None) -> None`

初始化日志对话框。

**参数**:
- `parent`: 父窗口部件

**示例**:
```python
dialog = LogDialog(parent=self)
dialog.exec_()
```

##### `load_file_list(self) -> None`

加载日志目录下的所有日志文件。

**副作用**:
- 清空文件列表控件
- 填充新的日志文件列表
- 自动加载第一个文件（如果存在）

##### `perform_search(self, direction: str = 'down') -> int`

执行搜索操作。

**参数**:
- `direction`: 搜索方向 ('up' 或 'down')

**返回**:
- int: 找到的匹配数量

**示例**:
```python
count = dialog.perform_search('down')
print(f"找到 {count} 个匹配")
```

##### `export_log(self, file_path: str) -> bool`

导出日志到文件。

**参数**:
- `file_path`: 目标文件路径

**返回**:
- bool: 导出是否成功

---

### GUIErrorHandler

统一的错误处理器。

```python
from src.presentation.dialogs.gui_utils import GUIErrorHandler

GUIErrorHandler.handle_error(
    context="加载文件",
    error=exc,
    show_dialog=True,
    parent=self
)
```

#### 方法

##### `handle_error(context: str, error: Exception, show_dialog: bool = False, parent: Optional[Any] = None, logger_instance: Optional[logging.Logger] = None) -> None`

统一处理错误。

**参数**:
- `context`: 错误上下文描述
- `error`: 异常对象
- `show_dialog`: 是否显示错误对话框
- `parent`: 父窗口部件
- `logger_instance`: 日志记录器实例

---

### FileUtils

文件操作工具类。

```python
from src.presentation.dialogs.gui_utils import FileUtils

# 检查是否为日志文件
is_log = FileUtils.is_log_file("app.log")  # True

# 分离文件名和扩展名
name, ext = FileUtils.split_extension("app.log")  # ('app', '.log')
```

#### 方法

| 方法 | 说明 |
|------|------|
| `get_file_extension(filename)` | 获取文件扩展名 |
| `split_extension(filename)` | 分离文件名和扩展名 |
| `is_log_file(filename, extensions)` | 检查是否为日志文件 |

---

### StringUtils

字符串操作工具类。

```python
from src.presentation.dialogs.gui_utils import StringUtils

# 截断字符串
truncated = StringUtils.truncate("很长很长的文本", 10)  # "很长很长的..."

# 脱敏处理
masked = StringUtils.mask_sensitive("password123", 4)  # "pass****"
```

#### 方法

| 方法 | 说明 |
|------|------|
| `truncate(text, max_length, suffix)` | 截断字符串 |
| `mask_sensitive(text, show_length)` | 脱敏处理 |

---

## 常量定义

### log_dialog.py

```python
# 默认日志目录
DEFAULT_LOG_DIR: str = "src/log"

# 支持的日志文件扩展名
LOG_FILE_EXTENSIONS: Tuple[str, ...] = ('.log', '.txt', '.LOG')

# 模块级配置标志
CONFIG_MANAGER_AVAILABLE: bool = True
```

### data_analysis_dialog.py

```python
# 数据预览相关常量
PREVIEW_ROWS: int = 50           # 预览行数
PREVIEW_BATCH_SIZE: int = 10     # 预览分批加载大小

# 图表相关常量
CHART_WIDTH: int = 400          # 图表默认宽度
CHART_HEIGHT: int = 400         # 图表默认高度

# 统计表格常量
STATS_COLUMN_COUNT: int = 9      # 统计表格列数
```

---

## 使用示例

### 1. 创建并使用 LogDialog

```python
from src.presentation.dialogs.log_dialog import LogDialog

# 在主窗口中打开日志对话框
def open_log_viewer(self):
    dialog = LogDialog(parent=self)
    if dialog.exec_() == QDialog.Accepted:
        print("日志查看完成")
```

### 2. 使用 GUIErrorHandler 处理错误

```python
from src.presentation.dialogs.gui_utils import GUIErrorHandler

try:
    # 可能抛出异常的操作
    self.load_data()
except Exception as e:
    GUIErrorHandler.handle_error(
        context="加载数据",
        error=e,
        show_dialog=True,
        parent=self,
        logger_instance=logger
    )
```

### 3. 使用 FileUtils 检查文件

```python
from src.presentation.dialogs.gui_utils import FileUtils

filename = "error.log"
if FileUtils.is_log_file(filename):
    print(f"{filename} 是日志文件")
    name, ext = FileUtils.split_extension(filename)
    print(f"文件扩展名: {ext}")
```

---

## 版本历史

| 版本 | 日期 | 更改 |
|------|------|------|
| 1.0 | 2024-01-01 | 初始版本 |
| 1.1 | 2024-01-15 | 添加 GUIErrorHandler |
| 1.2 | 2024-02-01 | 添加 FileUtils, StringUtils |

---

## 注意事项

1. **线程安全**: 所有 GUI 操作必须在主线程执行
2. **内存管理**: 大文件加载使用异步线程
3. **错误处理**: 使用 GUIErrorHandler 统一处理
4. **配置管理**: 支持从 ConfigManager 获取配置
