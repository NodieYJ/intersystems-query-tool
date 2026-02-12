#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异常处理装饰器和上下文管理器

提供便捷的异常处理机制，包括：
- 异常处理装饰器
- 异常处理上下文管理器
- 重试机制装饰器
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from src.infrastructure.exceptions.exceptions import (
    AppException,
    DatabaseException,
    BusinessException,
    ConfigurationException,
    ServiceException,
)

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class ExceptionHandler:
    """
    异常处理器类
    
    提供统一的异常处理和转换功能。
    
    示例:
        >>> handler = ExceptionHandler()
        >>> result = handler.handle(some_function, args, kwargs)
    """
    
    # 异常映射表：原始异常类型 -> 应用异常类型
    EXCEPTION_MAP: Dict[Type[Exception], Type[AppException]] = {
        ConnectionError: DatabaseException,
        TimeoutError: DatabaseException,
        FileNotFoundError: ConfigurationException,
        PermissionError: ConfigurationException,
        ValueError: BusinessException,
        TypeError: BusinessException,
        KeyError: BusinessException,
    }
    
    def __init__(
        self, 
        default_exception: Type[AppException] = AppException,
        error_code: str = "ERR_001",
        error_message: str = "操作失败",
        log_level: int = logging.ERROR
    ):
        """
        初始化异常处理器
        
        Args:
            default_exception: 默认异常类型
            error_code: 默认错误码
            error_message: 默认错误消息
            log_level: 日志级别
        """
        self.default_exception = default_exception
        self.error_code = error_code
        self.error_message = error_message
        self.log_level = log_level
    
    def handle(
        self, 
        func: Callable[..., Any], 
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        """
        执行函数并处理异常
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            AppException: 转换后的应用异常
        """
        try:
            return func(*args, **kwargs)
        except AppException:
            # 已经是应用异常，直接抛出
            raise
        except Exception as e:
            # 转换为应用异常
            converted = self._convert_exception(e)
            logger.log(self.log_level, f"Exception handled: {converted}", exc_info=True)
            raise converted
    
    def _convert_exception(self, original: Exception) -> AppException:
        """
        将原始异常转换为应用异常
        
        Args:
            original: 原始异常
            
        Returns:
            AppException: 转换后的异常
        """
        exception_type = type(original)
        
        # 查找映射的异常类型
        for source_type, target_type in self.EXCEPTION_MAP.items():
            if isinstance(original, source_type):
                return target_type(
                    error_code=self.error_code,
                    message=f"{self.error_message}: {str(original)}",
                    details={"original_exception": exception_type.__name__}
                )
        
        # 使用默认异常类型
        return self.default_exception(
            error_code=self.error_code,
            message=f"{self.error_message}: {str(original)}",
            details={"original_exception": exception_type.__name__}
        )


def handle_exceptions(
    exception_type: Type[AppException] = AppException,
    error_code: str = "ERR_001",
    error_message: str = "操作失败",
    log_level: int = logging.ERROR,
    reraise: bool = True
) -> Callable[[F], F]:
    """
    异常处理装饰器
    
    捕获函数执行中的异常，转换为应用异常并记录日志。
    
    Args:
        exception_type: 要抛出的异常类型
        error_code: 错误代码
        error_message: 错误消息
        log_level: 日志级别
        reraise: 是否重新抛出异常
        
    Returns:
        Callable: 装饰器函数
        
    示例:
        >>> @handle_exceptions(DatabaseException, "DB_001", "查询失败")
        ... def query_data(sql: str) -> List[Dict]:
        ...     return db.execute(sql)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except AppException:
                raise
            except Exception as e:
                exception = exception_type(
                    error_code=error_code,
                    message=f"{error_message}: {str(e)}",
                    details={
                        "function": func.__name__,
                        "original_exception": type(e).__name__
                    }
                )
                logger.log(log_level, f"Exception in {func.__name__}: {exception}", exc_info=True)
                
                if reraise:
                    raise exception
                return None
        
        return wrapper  # type: ignore
    return decorator


def retry_on_exception(
    exceptions: Union[Type[Exception], tuple] = Exception,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[F], F]:
    """
    重试装饰器
    
    在指定异常发生时自动重试函数执行。
    
    Args:
        exceptions: 要捕获的异常类型或类型元组
        max_retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍数
        on_retry: 重试时的回调函数，参数为(重试次数, 异常)
        
    Returns:
        Callable: 装饰器函数
        
    示例:
        >>> @retry_on_exception(DatabaseException, max_retries=3, delay=1.0)
        ... def connect_to_database() -> Connection:
        ...     return create_connection()
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {current_delay} seconds..."
                        )
                        
                        if on_retry:
                            on_retry(attempt + 1, e)
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts"
                        )
            
            # 所有重试都失败，抛出最后一个异常
            if last_exception:
                raise last_exception
            
            return None  # Should never reach here
        
        return wrapper  # type: ignore
    return decorator


class ExceptionContext:
    """
    异常处理上下文管理器
    
    使用with语句包裹代码块，统一处理异常。
    
    示例:
        >>> with ExceptionContext(DatabaseException, "DB_001", "数据库操作失败"):
        ...     db.execute("SELECT * FROM users")
        ...     db.commit()
    """
    
    def __init__(
        self,
        exception_type: Type[AppException] = AppException,
        error_code: str = "ERR_001",
        error_message: str = "操作失败",
        log_level: int = logging.ERROR,
        suppress: bool = False
    ):
        """
        初始化上下文管理器
        
        Args:
            exception_type: 异常类型
            error_code: 错误代码
            error_message: 错误消息
            log_level: 日志级别
            suppress: 是否抑制异常（不抛出）
        """
        self.exception_type = exception_type
        self.error_code = error_code
        self.error_message = error_message
        self.log_level = log_level
        self.suppress = suppress
    
    def __enter__(self) -> 'ExceptionContext':
        """进入上下文"""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        退出上下文，处理异常
        
        Returns:
            bool: True表示异常已处理，False表示继续抛出
        """
        if exc_val is None:
            return True
        
        if isinstance(exc_val, AppException):
            # 已经是应用异常，记录日志
            logger.log(self.log_level, f"Exception in context: {exc_val}", exc_info=True)
            return self.suppress
        
        # 转换为应用异常
        exception = self.exception_type(
            error_code=self.error_code,
            message=f"{self.error_message}: {str(exc_val)}",
            details={"original_exception": exc_type.__name__ if exc_type else "Unknown"}
        )
        
        logger.log(self.log_level, f"Exception converted in context: {exception}", exc_info=True)
        
        if self.suppress:
            return True
        
        # 抛出转换后的异常
        raise exception


def safe_execute(
    func: Callable[..., Any],
    *args: Any,
    default: Any = None,
    exception_types: tuple = (Exception,),
    **kwargs: Any
) -> Any:
    """
    安全执行函数
    
    捕获指定异常，返回默认值而不是抛出异常。
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        default: 异常时的默认值
        exception_types: 要捕获的异常类型元组
        **kwargs: 关键字参数
        
    Returns:
        Any: 函数结果或默认值
        
    示例:
        >>> result = safe_execute(risky_function, arg1, arg2, default=[])
    """
    try:
        return func(*args, **kwargs)
    except exception_types as e:
        logger.warning(f"Function {func.__name__} failed, returning default: {e}")
        return default


class CircuitBreaker:
    """
    熔断器
    
    当失败次数超过阈值时，自动开启熔断，快速失败。
    
    状态:
        - CLOSED: 正常状态，请求正常通过
        - OPEN: 熔断状态，请求快速失败
        - HALF_OPEN: 半开状态，尝试恢复
    
    示例:
        >>> breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)
        >>> @breaker
        ... def call_external_api():
        ...     return requests.get("https://api.example.com")
    """
    
    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败次数阈值
            recovery_timeout: 恢复超时（秒）
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = self.STATE_CLOSED
    
    def __call__(self, func: F) -> F:
        """作为装饰器使用"""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.state == self.STATE_OPEN:
                if self._should_attempt_reset():
                    self.state = self.STATE_HALF_OPEN
                else:
                    raise ServiceException(
                        service_name=func.__name__,
                        message="Circuit breaker is OPEN",
                        details={"state": self.state}
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper  # type: ignore
    
    def _should_attempt_reset(self) -> bool:
        """检查是否应该尝试重置熔断器"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """处理成功"""
        self.failure_count = 0
        self.state = self.STATE_CLOSED
    
    def _on_failure(self) -> None:
        """处理失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.STATE_OPEN
            logger.error(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> str:
        """获取当前状态"""
        return self.state
