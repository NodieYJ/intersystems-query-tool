# 深入讨论：可维护性优化 - 异常处理体系

**讨论时间**：2026年2月11日 20:40:00  
**参与人员**：AI Assistant + 用户

---

## 一、当前异常处理现状分析

### 1.1 当前异常处理模式检查

```python
# 当前代码中的异常处理模式

# 模式1：捕获通用异常（最多）
try:
    result = some_operation()
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    return None

# 模式2：捕获特定异常（较少）
try:
    self.dataframe = pd.read_csv(file_path)
except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
    logger.error(f"CSV解析失败: {e}")
    return False

# 模式3：捕获并重新抛出
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    raise

# 模式4：全局异常处理（main.py）
try:
    app.run()
except tuple(exception_handlers.keys()) as e:
    title, suggestion = exception_handlers[exc_type]
```

### 1.2 问题统计

| 异常处理模式 | 出现次数 | 问题 |
|-------------|---------|------|
| `except Exception as e:` | 100+ | 太宽泛，无法区分错误类型 |
| `except Exception:` | 50+ | 丢失异常信息 |
| 特定异常 | 10+ | 不一致 |
| 无异常处理 | 20+ | 可能导致崩溃 |

### 1.3 当前问题清单

| # | 问题 | 影响 | 严重程度 |
|---|------|------|----------|
| **1** | 无自定义异常类 | 无法区分业务错误 | 🔴 高 |
| **2** | 异常信息不统一 | 难以排查问题 | 🔴 高 |
| **3** | 异常处理逻辑分散 | 维护困难 | 🟡 中 |
| **4** | 缺少错误码体系 | 难以追踪问题 | 🟡 中 |
| **5** | 全局处理不完整 | 用户体验差 | 🟡 中 |

---

## 二、异常处理体系设计

### 2.1 异常类层次结构

```python
# src/infrastructure/exceptions/__init__.py

from abc import ABC
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import traceback
import sys


class AppException(Exception):
    """
    应用基础异常类
    
    所有自定义异常的基类。
    提供统一的异常信息格式和错误追踪能力。
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "APP_000",
        details: Dict[str, Any] = None,
        cause: Exception = None
    ):
        """
        初始化应用异常
        
        Args:
            message: 异常消息（人类可读）
            error_code: 错误码（格式：模块_序号，如 DB_001）
            details: 额外详细信息字典
            cause: 原始异常（用于异常链）
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = self._get_timestamp()
        self.traceback_str = self._get_traceback()
    
    def _get_timestamp(self) -> str:
        """获取异常发生时间"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_traceback(self) -> str:
        """获取堆栈跟踪"""
        return traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp,
            "details": self.details,
            "traceback": self.traceback_str
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"[{self.error_code}] {self.message}"
    
    def log(self, logger):
        """记录异常日志"""
        logger.error(
            f"异常发生: {self.__str__()}",
            extra={
                "error_code": self.error_code,
                "details": self.details,
                "traceback": self.traceback_str
            },
            exc_info=True
        )


# ==================== 数据库异常 ====================

class DatabaseException(AppException):
    """
    数据库操作异常基类
    
    所有数据库相关异常的父类。
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "DB_000",
        sql: str = None,
        **kwargs
    ):
        """
        初始化数据库异常
        
        Args:
            message: 异常消息
            error_code: 错误码
            sql: 相关的SQL语句
            **kwargs: 其他参数
        """
        details = kwargs.get('details', {})
        details['sql'] = sql
        super().__init__(message, error_code, details, kwargs.get('cause'))


class ConnectionException(DatabaseException):
    """数据库连接异常"""
    
    def __init__(
        self,
        message: str = "数据库连接失败",
        connection_info: Dict = None,
        **kwargs
    ):
        details = {'connection_info': connection_info}
        super().__init__(
            message,
            error_code="DB_001",
            details=details,
            **kwargs
        )


class QueryExecutionException(DatabaseException):
    """查询执行异常"""
    
    def __init__(
        self,
        message: str = "查询执行失败",
        sql: str = None,
        parameters: list = None,
        execution_time: float = None,
        **kwargs
    ):
        details = {'sql': sql}
        if parameters:
            details['parameters'] = parameters
        if execution_time:
            details['execution_time'] = execution_time
        
        super().__init__(
            message,
            error_code="DB_002",
            details=details,
            **kwargs
        )


class TransactionException(DatabaseException):
    """事务执行异常"""
    
    def __init__(
        self,
        message: str = "事务执行失败",
        transaction_id: str = None,
        **kwargs
    ):
        details = {'transaction_id': transaction_id}
        super().__init__(
            message,
            error_code="DB_003",
            details=details,
            **kwargs
        )


# ==================== 业务异常 ====================

class BusinessException(AppException):
    """
    业务逻辑异常基类
    
    所有业务规则相关异常的父类。
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "BZ_000",
        entity: str = None,
        field: str = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if entity:
            details['entity'] = entity
        if field:
            details['field'] = field
        super().__init__(message, error_code, details, kwargs.get('cause'))


class ValidationException(BusinessException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = "数据验证失败",
        field: str = None,
        value: Any = None,
        rule: str = None,
        **kwargs
    ):
        details = {'field': field, 'value': value, 'rule': rule}
        super().__init__(
            message,
            error_code="BZ_001",
            details=details,
            **kwargs
        )


class NotFoundException(BusinessException):
    """资源不存在异常"""
    
    def __init__(
        self,
        message: str = "请求的资源不存在",
        resource_type: str = None,
        resource_id: Any = None,
        **kwargs
    ):
        details = {'resource_type': resource_type, 'resource_id': resource_id}
        super().__init__(
            message,
            error_code="BZ_002",
            details=details,
            **kwargs
        )


class DuplicateException(BusinessException):
    """重复操作异常"""
    
    def __init__(
        self,
        message: str = "资源已存在",
        resource_type: str = None,
        duplicate_field: str = None,
        **kwargs
    ):
        details = {'resource_type': resource_type, 'duplicate_field': duplicate_field}
        super().__init__(
            message,
            error_code="BZ_003",
            details=details,
            **kwargs
        )


# ==================== 配置异常 ====================

class ConfigurationException(AppException):
    """配置异常"""
    
    def __init__(
        self,
        message: str = "配置错误",
        config_key: str = None,
        expected_value: Any = None,
        actual_value: Any = None,
        **kwargs
    ):
        details = {'config_key': config_key}
        if expected_value:
            details['expected_value'] = expected_value
        if actual_value:
            details['actual_value'] = actual_value
        super().__init__(
            message,
            error_code="CFG_001",
            details=details,
            **kwargs
        )


# ==================== 数据异常 ====================

class DataException(AppException):
    """数据处理异常"""
    
    def __init__(
        self,
        message: str = "数据处理错误",
        data_operation: str = None,
        data_source: str = None,
        **kwargs
    ):
        details = {'data_operation': data_operation, 'data_source': data_source}
        super().__init__(
            message,
            error_code="DATA_001",
            details=details,
            **kwargs
        )


class DataParsingException(DataException):
    """数据解析异常"""
    
    def __init__(
        self,
        message: str = "数据解析失败",
        format: str = None,
        line_number: int = None,
        **kwargs
    ):
        details = {'format': format, 'line_number': line_number}
        super().__init__(
            message,
            error_code="DATA_002",
            details=details,
            **kwargs
        )


class DataConversionException(DataException):
    """数据转换异常"""
    
    def __init__(
        self,
        message: str = "数据转换失败",
        source_type: str = None,
        target_type: str = None,
        value: Any = None,
        **kwargs
    ):
        details = {
            'source_type': source_type,
            'target_type': target_type,
            'value': str(value)
        }
        super().__init__(
            message,
            error_code="DATA_003",
            details=details,
            **kwargs
        )
```

### 2.2 异常处理装饰器

```python
# src/infrastructure/exceptions/decorators.py

import logging
from functools import wraps
from typing import Callable, Type

logger = logging.getLogger(__name__)


def handle_exceptions(
    default_return: Any = None,
    exception_map: Dict[Type[Exception], Callable] = None,
    reraise: bool = False,
    log_level: str = "error"
):
    """
    异常处理装饰器
    
    统一处理方法中的异常，提供灵活的异常处理策略。
    
    Args:
        default_return: 默认返回值（发生异常时返回）
        exception_map: 异常类型到处理函数的映射
        reraise: 是否重新抛出异常
        log_level: 日志级别
    
    Example:
        @handle_exceptions(default_return=None, log_level="warning")
        def risky_operation():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            
            except AppException as e:
                # 应用异常已包含完整信息，直接记录
                e.log(logger)
                
                if exception_map and type(e) in exception_map:
                    return exception_map[type(e)](e)
                
                return default_return
            
            except Exception as e:
                # 转换为应用异常
                app_exc = AppException(
                    message=str(e),
                    error_code="APP_999",
                    cause=e
                )
                app_exc.log(logger)
                
                if exception_map:
                    for exc_type, handler in exception_map.items():
                        if isinstance(e, exc_type):
                            return handler(e)
                
                if reraise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    重试装饰器
    
    在发生异常时自动重试操作。
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间倍增因子
        exceptions: 需要重试的异常类型
    
    Example:
        @retry(max_attempts=3, delay=1.0)
        def connect_to_database():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # 最后一次尝试，重新抛出
                        raise
                    
                    logger.warning(
                        f"第 {attempt + 1} 次尝试失败，"
                        f"等待 {current_delay:.1f} 秒后重试: {str(e)}"
                    )
                    
                    import time
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator
```

### 2.3 全局异常处理器

```python
# src/infrastructure/exceptions/handlers.py

import sys
import logging
from typing import Dict, Tuple, Callable
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ExceptionHandler(QObject):
    """
    全局异常处理器
    
    捕获未处理的异常，提供统一的处理策略。
    """
    
    # 信号：异常发生时发射
    exception_occurred = Signal(object)
    
    # 错误码到用户消息的映射
    USER_MESSAGES: Dict[str, Tuple[str, str]] = {
        "DB_001": ("数据库连接失败", "请检查数据库配置是否正确"),
        "DB_002": ("查询执行失败", "请检查SQL语句是否正确"),
        "BZ_001": ("数据验证失败", "请检查输入数据的格式"),
        "BZ_002": ("资源不存在", "请确认请求的资源是否存在"),
        "CFG_001": ("配置错误", "请检查配置文件是否正确"),
        "DATA_001": ("数据处理错误", "请检查数据格式是否正确"),
        "APP_999": ("系统错误", "请查看日志获取详细信息"),
    }
    
    def __init__(self):
        super().__init__()
        self._original_excepthook = sys.excepthook
        self._setup_excepthook()
    
    def _setup_excepthook(self):
        """设置全局异常钩子"""
        sys.excepthook = self._handle_exception
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """全局异常处理回调"""
        # 构建应用异常
        app_exc = AppException(
            message=str(exc_value),
            error_code=self._get_error_code(exc_type),
            cause=exc_value
        )
        
        # 记录日志
        app_exc.log(logger)
        
        # 发射信号
        self.exception_occurred.emit(app_exc)
        
        # 调用原始处理（可选）
        # self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _get_error_code(self, exc_type: type) -> str:
        """根据异常类型获取错误码"""
        code_mapping = {
            ConnectionError: "DB_001",
            RuntimeError: "APP_999",
            ValueError: "BZ_001",
            KeyError: "BZ_002",
        }
        
        for base_type, code in code_mapping.items():
            if issubclass(exc_type, base_type):
                return code
        
        return "APP_999"
    
    def get_user_message(self, error_code: str) -> Tuple[str, str]:
        """
        获取用户友好的错误消息
        
        Args:
            error_code: 错误码
        
        Returns:
            Tuple[str, str]: (标题, 建议)
        """
        return self.USER_MESSAGES.get(error_code, (
            "发生错误",
            "请查看日志获取详细信息"
        ))
    
    def show_error_dialog(self, parent, exception: AppException):
        """
        显示错误对话框
        
        Args:
            parent: 父窗口
            exception: 异常对象
        """
        title, suggestion = self.get_user_message(exception.error_code)
        
        # 构建详细消息
        message = f"{exception.message}\n\n建议: {suggestion}"
        
        # 添加调试信息（仅开发环境显示）
        import os
        if os.environ.get("DEBUG_MODE"):
            message += f"\n\n错误码: {exception.error_code}"
            message += f"\n时间: {exception.timestamp}"
        
        QMessageBox.critical(parent, title, message)
```

### 2.4 使用示例

```python
# src/business/services/data_service.py 优化版

from src.infrastructure.exceptions import (
    AppException,
    DatabaseException,
    QueryExecutionException,
    ValidationException,
    handle_exceptions,
)
from src.infrastructure.exceptions.decorators import retry

class DataService:
    """数据服务（优化版异常处理）"""
    
    def __init__(self, db_repository):
        self.db_repository = db_repository
    
    @handle_exceptions(default_return=None, reraise=True)
    def get_data(
        self, 
        query: str, 
        params: list = None
    ) -> list:
        """
        获取数据
        
        Raises:
            ValidationException: 查询语句为空
            QueryExecutionException: 查询执行失败
        """
        # 验证输入
        if not query or not query.strip():
            raise ValidationException(
                message="查询语句不能为空",
                field="query",
                value=query,
                rule="not_empty"
            )
        
        try:
            # 执行查询
            result = self.db_repository.execute_query(query, params)
            return result
        
        except Exception as e:
            raise QueryExecutionException(
                message=f"查询执行失败: {str(e)}",
                sql=query,
                parameters=params,
                cause=e
            )
    
    @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
    def test_connection(self) -> bool:
        """测试数据库连接（支持重试）"""
        return self.db_repository.execute_query("SELECT 1")
```

---

## 三、异常处理最佳实践

### 3.1 异常处理规范

| 场景 | 推荐做法 | 不推荐做法 |
|------|---------|-----------|
| 参数验证 | 抛出 `ValidationException` | 静默返回 None |
| 外部调用 | 使用 `@handle_exceptions` | try-catch 包裹每个调用 |
| 资源获取 | 使用 `@retry` | 无限重试 |
| 业务规则 | 抛出 `BusinessException` | 返回错误码 |
| 系统错误 | 记录并重新抛出 | 隐藏错误 |

### 3.2 错误码规范

```
错误码格式：模块_序号

模块前缀：
- APP: 应用基础异常
- DB: 数据库异常
- BZ: 业务异常
- CFG: 配置异常
- DATA: 数据处理异常

示例：
- APP_001: 未知错误
- APP_999: 系统内部错误
- DB_001: 连接失败
- DB_002: 查询失败
- BZ_001: 验证失败
- BZ_002: 资源不存在
```

---

## 四、实施步骤

### 阶段1：创建异常体系（0.5天）

1. 创建 `src/infrastructure/exceptions/` 目录
2. 实现自定义异常类
3. 实现异常处理装饰器
4. 实现全局异常处理器

### 阶段2：重构现有代码（1周）

1. 识别所有 `except Exception` 块
2. 替换为适当的自定义异常
3. 添加必要的数据验证
4. 更新日志记录

### 阶段3：测试验证（0.5天）

1. 单元测试异常处理
2. 集成测试错误场景
3. 验证用户错误提示

---

## 五、预期效果

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| **异常可识别性** | 低 | 高 | +150% |
| **问题排查速度** | 慢 | 快 | +100% |
| **代码一致性** | 低 | 高 | +200% |
| **用户体验** | 差 | 好 | +80% |

---

## 六、风险和缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 改动范围过大 | 中 | 高 | 分阶段实施 |
| 性能影响 | 低 | 低 | 装饰器开销很小 |
| 异常信息泄露 | 低 | 中 | 敏感信息过滤 |

---

## 讨论记录

| 时间 | 讨论内容 | 结论 |
|------|----------|------|
| 20:40 | 当前异常处理分析 | 发现无自定义异常类 |
| 20:45 | 问题严重程度评估 | 影响问题排查和用户体验 |
| 20:50 | 解决方案设计 | 确定分层异常体系方案 |

---

**讨论状态**：✅ 异常处理体系设计完成  
**下一步**：继续讨论代码注释和文档  
**预计继续时间**：2026年2月11日 21:10:00
