# 线程安全最佳实践指南

## 概述

本文档总结了 PySide2 桌面应用程序中的线程安全最佳实践，基于代码审查中发现的问题和修复经验。

## 核心原则

### 1. 主线程绝不能阻塞

**规则**: 所有耗时的操作（数据库查询、网络请求、文件 I/O）必须在后台线程执行。

**错误示例**:
```python
# 错误: 在主线程执行数据库查询
def show_available_tables(self):
    result = self.data_service.get_data("SELECT ...")  # 阻塞主线程!
    self.update_table_list(result)
```

**正确示例**:
```python
# 正确: 使用后台线程
def show_available_tables(self):
    self.load_database_objects_async()  # 使用已有的异步方法

def load_database_objects_async(self):
    """异步加载数据库对象"""
    loader = DatabaseObjectLoader(self.data_service)
    loader.objects_loaded.connect(self.on_objects_loaded)
    loader.start()
```

### 2. 跨线程通信必须使用信号槽

**规则**: 线程间通信必须使用 Qt 的信号槽机制，不能直接访问其他线程的对象。

**错误示例**:
```python
# 错误: 直接访问其他线程的对象
def run(self):
    result = self.data_service.query()
    self.parent().update_ui(result)  # 直接调用主线程方法!
```

**正确示例**:
```python
# 正确: 使用信号槽
class DatabaseLoader(QThread):
    objects_loaded = Signal(list)
    error = Signal(str)

    def run(self):
        try:
            result = self.data_service.query()
            self.objects_loaded.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

### 3. 正确管理线程生命周期

**规则**: 线程完成后必须正确清理，避免内存泄漏。

**正确示例**:
```python
def load_data_async(self):
    loader = DatabaseLoader()

    # 使用 Qt.AutoConnection 确保跨线程信号安全
    loader.objects_loaded.connect(self.on_data_loaded, Qt.AutoConnection)
    loader.error.connect(self.on_error, Qt.AutoConnection)

    # 线程完成后自动删除
    loader.finished.connect(loader.deleteLater)

    loader.start()
```

## 线程安全实践清单

### 必须做

- [ ] 所有数据库操作在后台线程执行
- [ ] 使用 `QThread` 或 `QRunnable` + `QThreadPool`
- [ ] 线程间通信使用信号槽
- [ ] 使用 `Qt.AutoConnection` 连接跨线程信号
- [ ] 线程完成后调用 `deleteLater()` 或手动删除
- [ ] 使用 `wait()` 等待线程完成（如果需要）

### 禁止做

- [ ] 在主线程执行耗时操作
- [ ] 直接调用其他线程的对象方法
- [ ] 在子线程访问 UI 组件
- [ ] 使用 lambda 表达式连接信号槽（可能导致内存泄漏）
- [ ] 持有线程对象的强引用不释放

## 内存泄漏防护

### 问题场景

```python
# 问题: lambda 捕获变量可能导致问题
worker = QueryWorker(sql)
worker.signals.result.connect(lambda r: self.on_result(r, tab))  # 可能导致问题
```

### 解决方案

```python
# 方案1: 在 Worker 中存储引用
class QueryWorker(QRunnable):
    def __init__(self, query: str, tab: 'QueryTab'):
        super().__init__()
        self.query = query
        self.tab = tab  # 存储引用

    def run(self):
        result = self.data_service.query()
        self.signals.result.emit(result)

# 使用
worker = QueryWorker(sql, tab=self.current_tab)
worker.signals.result.connect(self.on_result)  # 不用 lambda
```

## 常见模式

### 模式1: 异步数据加载

```python
class AsyncDataLoader(QThread):
    """异步数据加载器"""
    loaded = Signal(object)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, data_service, query):
        super().__init__()
        self.data_service = data_service
        self.query = query

    def run(self):
        try:
            self.progress.emit(0)
            # 执行查询
            result = self.data_service.get_data(self.query)
            self.progress.emit(100)
            self.loaded.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# 使用
loader = AsyncDataLoader(self.data_service, query)
loader.loaded.connect(self.handle_result)
loader.error.connect(self.handle_error)
loader.finished.connect(loader.deleteLater)
loader.start()
```

### 模式2: 进度报告

```python
class ProgressWorker(QRunnable):
    """带进度报告的工作线程"""
    progress = Signal(int)
    finished = Signal(object)

    def run(self):
        total = 100
        for i in range(total):
            # 执行工作
            self.progress.emit(int((i / total) * 100))
        self.finished.emit(result)
```

### 模式3: 超时控制

```python
class TimeoutWorker(QThread):
    """带超时控制的工作线程"""
    finished = Signal(object)
    timeout = Signal()

    def __init__(self, timeout_ms=5000):
        super().__init__()
        self.timeout_ms = timeout_ms

    def run(self):
        worker = LongRunningTask()
        worker.start()

        # 等待完成或超时
        if worker.wait(self.timeout_ms):
            self.finished.emit(worker.result)
        else:
            worker.terminate()
            self.timeout.emit()
```

## 代码审查修复记录

### 已修复的问题

| 问题 | 文件 | 修复方案 |
|------|------|----------|
| 主线程执行数据库查询 | `sql_query_dialog.py` | 改用异步方法 |
| 内存泄漏 | `sql_query_dialog.py` | 添加 `finished.connect(deleteLater)` |
| lambda 信号连接 | `sql_query_dialog.py` | 重构为显式方法引用 |
| 配置路径硬编码 | `connection_config_dialog.py` | 使用 `ConfigManager` |
| 密码日志泄露 | `connection_config_dialog.py` | 移除密码长度日志 |

## 测试策略

### 单元测试

```python
def test_query_worker_creation(self):
    worker = QueryWorker("SELECT 1", tab=None)
    assert worker.query == "SELECT 1"
    assert worker.tab is None
```

### 集成测试

```python
def test_async_loading(self):
    """测试异步加载流程"""
    loader = DatabaseObjectLoader(mock_service)
    loader.objects_loaded.emit(mock_data)

    # 验证信号已发送
    # 验证数据已处理
```

### UI 测试 (pytest-qt)

```python
def test_dialog_creation(self, qtbot):
    """测试对话框创建"""
    dialog = ConnectionConfigDialog()
    qtbot.addWidget(dialog)
    assert dialog.isVisible()
```

## 性能考虑

### 线程池配置

```python
# 配置线程池
self.thread_pool = QThreadPool()
self.thread_pool.setMaxThreadCount(4)  # 根据CPU核心数调整
self.thread_pool.setExpiryTimeout(30000)  # 30秒超时
```

### 避免过度线程化

- 小任务直接同步执行
- 批量操作使用批量查询
- 使用缓存减少重复查询

## 监控和调试

### 日志记录

```python
logger.info("开始异步加载")
logger.debug(f"线程状态: {loader.isRunning()}")
logger.info("异步加载完成")
```

### 调试技巧

1. 使用 `QThread.currentThread()` 验证线程
2. 使用 `Qt.Checked` 连接类型验证
3. 使用 `logger.debug()` 跟踪线程生命周期

## 参考资料

- [Qt Threading Basics](https://doc.qt.io/qt-5/thread-basics.html)
- [Qt Thread Support in Qt](https://doc.qt.io/qt-5/threads-qobject.html)
- [PySide2 Threading](https://doc.qt.io/qtforpython-5/overviews/threading.html)
