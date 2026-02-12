#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用程序异常体系

定义项目中使用的所有自定义异常类，提供统一的异常处理机制。
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    应用程序基础异常类
    
    所有自定义异常的基类，提供统一的错误码和错误信息格式。
    
    Attributes:
        error_code: 错误代码
        message: 错误信息
        details: 详细错误信息字典
    
    示例:
        >>> raise AppException("ERR_001", "数据库连接失败")
        >>> raise AppException("ERR_002", "用户不存在", details={"user_id": 123})
    """
    
    def __init__(
        self, 
        error_code: str, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        初始化异常
        
        Args:
            error_code: 错误代码，格式如 "ERR_001"
            message: 错误描述信息
            details: 详细错误信息字典，可选
        """
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """返回格式化的错误信息"""
        if self.details:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将异常转换为字典格式
        
        Returns:
            Dict[str, Any]: 包含错误信息的字典
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "exception_type": self.__class__.__name__
        }


class DatabaseException(AppException):
    """
    数据库操作异常
    
    数据库连接、查询、更新等操作失败时抛出。
    
    示例:
        >>> raise DatabaseException("DB_001", "连接超时", {"server": "localhost"})
    """
    
    def __init__(
        self, 
        error_code: str = "DB_001",
        message: str = "数据库操作失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(error_code, message, details)


class ConnectionException(DatabaseException):
    """
    数据库连接异常
    
    连接建立、断开或连接池相关错误。
    """
    
    def __init__(
        self, 
        message: str = "数据库连接失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("DB_002", message, details)


class QueryException(DatabaseException):
    """
    SQL查询异常
    
    SQL语句执行失败、语法错误等。
    """
    
    def __init__(
        self, 
        message: str = "查询执行失败", 
        sql: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if sql:
            error_details["sql"] = sql
        super().__init__("DB_003", message, error_details)


class TransactionException(DatabaseException):
    """
    事务异常
    
    事务提交、回滚失败。
    """
    
    def __init__(
        self, 
        message: str = "事务操作失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("DB_004", message, details)


class BusinessException(AppException):
    """
    业务逻辑异常
    
    业务规则校验失败时抛出。
    
    示例:
        >>> raise BusinessException("BIZ_001", "用户名已存在")
    """
    
    def __init__(
        self, 
        error_code: str = "BIZ_001",
        message: str = "业务处理失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(error_code, message, details)


class ValidationException(BusinessException):
    """
    数据校验异常
    
    输入数据格式、范围、类型等校验失败。
    """
    
    def __init__(
        self, 
        message: str = "数据校验失败", 
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__("BIZ_002", message, error_details)


class NotFoundException(BusinessException):
    """
    资源不存在异常
    
    查询的资源不存在时抛出。
    """
    
    def __init__(
        self, 
        resource_type: str = "Resource",
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type}"
        if resource_id:
            message += f" (ID: {resource_id})"
        message += " 不存在"
        
        error_details = details or {}
        error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
            
        super().__init__("BIZ_003", message, error_details)


class DuplicateException(BusinessException):
    """
    资源重复异常
    
    创建的资源已存在时抛出。
    """
    
    def __init__(
        self, 
        resource_type: str = "Resource",
        identifier: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type}"
        if identifier:
            message += f" ({identifier})"
        message += " 已存在"
        
        error_details = details or {}
        error_details["resource_type"] = resource_type
        if identifier:
            error_details["identifier"] = identifier
            
        super().__init__("BIZ_004", message, error_details)


class ConfigurationException(AppException):
    """
    配置异常
    
    配置读取、验证、解析失败时抛出。
    
    示例:
        >>> raise ConfigurationException("CFG_001", "缺少必需配置项: database.host")
    """
    
    def __init__(
        self, 
        error_code: str = "CFG_001",
        message: str = "配置错误", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(error_code, message, details)


class ConfigNotFoundException(ConfigurationException):
    """
    配置文件不存在异常
    """
    
    def __init__(
        self, 
        config_path: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["config_path"] = config_path
        super().__init__("CFG_002", f"配置文件不存在: {config_path}", error_details)


class ConfigParseException(ConfigurationException):
    """
    配置解析异常
    """
    
    def __init__(
        self, 
        config_path: str,
        parse_error: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["config_path"] = config_path
        error_details["parse_error"] = parse_error
        super().__init__("CFG_003", f"配置解析失败: {parse_error}", error_details)


class ConfigValidationException(ConfigurationException):
    """
    配置验证异常
    """
    
    def __init__(
        self, 
        field: str,
        value: Any,
        expected_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["field"] = field
        error_details["value"] = value
        error_details["expected_type"] = expected_type
        message = f"配置项 '{field}' 验证失败，期望类型: {expected_type}"
        super().__init__("CFG_004", message, error_details)


class SecurityException(AppException):
    """
    安全异常
    
    密码加密、解密、权限校验等安全相关错误。
    
    示例:
        >>> raise SecurityException("SEC_001", "密码加密失败")
    """
    
    def __init__(
        self, 
        error_code: str = "SEC_001",
        message: str = "安全错误", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(error_code, message, details)


class EncryptionException(SecurityException):
    """
    加密异常
    """
    
    def __init__(
        self, 
        message: str = "加密操作失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("SEC_002", message, details)


class DecryptionException(SecurityException):
    """
    解密异常
    """
    
    def __init__(
        self, 
        message: str = "解密操作失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("SEC_003", message, details)


class PermissionException(SecurityException):
    """
    权限异常
    """
    
    def __init__(
        self, 
        message: str = "权限不足", 
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
        super().__init__("SEC_004", message, error_details)


class ServiceException(AppException):
    """
    服务层异常
    
    业务服务调用失败。
    
    示例:
        >>> raise ServiceException("SRV_001", "数据服务初始化失败")
    """
    
    def __init__(
        self, 
        service_name: str,
        message: str = "服务调用失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["service_name"] = service_name
        super().__init__("SRV_001", f"[{service_name}] {message}", error_details)


class ServiceNotInitializedException(ServiceException):
    """
    服务未初始化异常
    """
    
    def __init__(
        self, 
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(service_name, "服务未初始化", details)


class ExternalServiceException(AppException):
    """
    外部服务异常
    
    调用第三方服务失败时抛出。
    """
    
    def __init__(
        self, 
        service_name: str,
        message: str = "外部服务调用失败", 
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["external_service"] = service_name
        super().__init__("EXT_001", f"[{service_name}] {message}", error_details)


class TimeoutException(AppException):
    """
    超时异常
    
    操作执行超时。
    """
    
    def __init__(
        self, 
        operation: str,
        timeout_seconds: float,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["operation"] = operation
        error_details["timeout_seconds"] = timeout_seconds
        message = f"操作 '{operation}' 超时 ({timeout_seconds}秒)"
        super().__init__("TIME_001", message, error_details)


class SystemException(AppException):
    """
    系统级异常
    
    系统资源不足、文件系统错误等底层错误。
    """
    
    def __init__(
        self, 
        error_code: str = "SYS_001",
        message: str = "系统错误", 
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(error_code, message, details)


class FileSystemException(SystemException):
    """
    文件系统异常
    """
    
    def __init__(
        self, 
        file_path: str,
        operation: str = "access",
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        error_details["file_path"] = file_path
        error_details["operation"] = operation
        message = f"文件操作失败 [{operation}]: {file_path}"
        super().__init__("SYS_002", message, error_details)


class MemoryException(SystemException):
    """
    内存异常
    """
    
    def __init__(
        self, 
        message: str = "内存不足", 
        requested_bytes: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_details = details or {}
        if requested_bytes:
            error_details["requested_bytes"] = requested_bytes
        super().__init__("SYS_003", message, error_details)


def get_exception_hierarchy() -> Dict[str, type]:
    """
    获取所有异常类的层级关系
    
    Returns:
        Dict[str, type]: 异常类名字到类的映射
    """
    return {
        # 基础异常
        "AppException": AppException,
        
        # 数据库异常
        "DatabaseException": DatabaseException,
        "ConnectionException": ConnectionException,
        "QueryException": QueryException,
        "TransactionException": TransactionException,
        
        # 业务异常
        "BusinessException": BusinessException,
        "ValidationException": ValidationException,
        "NotFoundException": NotFoundException,
        "DuplicateException": DuplicateException,
        
        # 配置异常
        "ConfigurationException": ConfigurationException,
        "ConfigNotFoundException": ConfigNotFoundException,
        "ConfigParseException": ConfigParseException,
        "ConfigValidationException": ConfigValidationException,
        
        # 安全异常
        "SecurityException": SecurityException,
        "EncryptionException": EncryptionException,
        "DecryptionException": DecryptionException,
        "PermissionException": PermissionException,
        
        # 服务异常
        "ServiceException": ServiceException,
        "ServiceNotInitializedException": ServiceNotInitializedException,
        "ExternalServiceException": ExternalServiceException,
        
        # 其他异常
        "TimeoutException": TimeoutException,
        "SystemException": SystemException,
        "FileSystemException": FileSystemException,
        "MemoryException": MemoryException,
    }
