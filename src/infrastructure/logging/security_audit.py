#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全审计日志模块

提供安全相关事件的审计日志功能
"""

import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
  """安全事件类型"""

  # 认证事件
  LOGIN_SUCCESS = "LOGIN_SUCCESS"
  LOGIN_FAILED = "LOGIN_FAILED"
  LOGOUT = "LOGOUT"
  PASSWORD_CHANGE = "PASSWORD_CHANGE"
  PASSWORD_RESET = "PASSWORD_RESET"

  # 授权事件
  ACCESS_DENIED = "ACCESS_DENIED"
  PRIVILEGE_CHANGE = "PRIVILEGE_CHANGE"

  # 数据事件
  SENSITIVE_DATA_ACCESS = "SENSITIVE_DATA_ACCESS"
  BULK_DATA_EXPORT = "BULK_DATA_EXPORT"
  DATA_MODIFICATION = "DATA_MODIFICATION"

  # 系统事件
  CONFIG_CHANGE = "CONFIG_CHANGE"
  SERVICE_RESTART = "SERVICE_RESTART"
  SCHEMA_CHANGE = "SCHEMA_CHANGE"

  # 安全事件
  SQL_INJECTION_ATTEMPT = "SQL_INJECTION_ATTEMPT"
  INVALID_INPUT_DETECTED = "INVALID_INPUT_DETECTED"
  ENCRYPTION_FAILURE = "ENCRYPTION_FAILURE"
  SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"


class SecurityAuditLogger:
  """
  安全审计日志器

  记录所有安全相关事件
  """

  def __init__(
    self,
    log_file: str = "logs/security_audit.log",
    level: int = logging.INFO,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
  ):
    """
    初始化安全审计日志器

    Args:
        log_file: 日志文件路径
        level: 日志级别
        max_file_size: 最大文件大小（字节）
        backup_count: 保留的备份文件数量
    """
    self.log_file = log_file
    self.level = level
    self.max_file_size = max_file_size
    self.backup_count = backup_count

    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
      os.makedirs(log_dir)

    # 设置日志格式
    self.formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建文件处理器
    self._setup_file_handler()

    # 创建控制台处理器
    self._setup_console_handler()

  def _setup_file_handler(self) -> None:
    """设置文件处理器"""
    self.file_handler = logging.FileHandler(
      self.log_file,
      encoding='utf-8'
    )
    self.file_handler.setLevel(self.level)
    self.file_handler.setFormatter(self.formatter)
    logger.addHandler(self.file_handler)

  def _setup_console_handler(self) -> None:
    """设置控制台处理器"""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # 只输出警告及以上
    console_handler.setFormatter(self.formatter)
    logger.addHandler(console_handler)

  def _check_file_rotation(self) -> None:
    """检查文件大小并轮转"""
    if os.path.exists(self.log_file):
      file_size = os.path.getsize(self.log_file)
      if file_size >= self.max_file_size:
        self._rotate_logs()

  def _rotate_logs(self) -> None:
    """轮转日志文件"""
    for i in range(self.backup_count - 1, 0, -1):
      src = f"{self.log_file}.{i}" if i > 1 else self.log_file
      dst = f"{self.log_file}.{i + 1}"
      if os.path.exists(src):
        os.rename(src, dst)

    if os.path.exists(self.log_file):
      os.rename(self.log_file, f"{self.log_file}.1")

  def log_event(
    self,
    event_type: SecurityEventType,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    message: Optional[str] = None
  ) -> Dict[str, Any]:
    """
    记录安全事件

    Args:
        event_type: 事件类型
        user_id: 用户ID
        ip_address: IP 地址
        details: 详细信息
        success: 是否成功
        message: 附加消息

    Returns:
        Dict[str, Any]: 事件记录
    """
    # 构建事件记录
    event_record = {
      "timestamp": datetime.now().isoformat(),
      "event_type": event_type.value,
      "user_id": user_id,
      "ip_address": ip_address,
      "success": success,
      "message": message,
      "details": details or {}
    }

    # 检查日志轮转
    self._check_file_rotation()

    # 记录日志
    log_level = logging.INFO if success else logging.WARNING
    log_message = json.dumps(event_record, ensure_ascii=False)

    logger.log(log_level, log_message, extra={'event': event_record})

    return event_record

  # ========== 便捷方法 ==========

  def log_login_success(
    self,
    user_id: str,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
  ) -> Dict[str, Any]:
    """记录登录成功"""
    return self.log_event(
      event_type=SecurityEventType.LOGIN_SUCCESS,
      user_id=user_id,
      ip_address=ip_address,
      success=True,
      details=details
    )

  def log_login_failed(
    self,
    user_id: str,
    ip_address: Optional[str] = None,
    reason: Optional[str] = None
  ) -> Dict[str, Any]:
    """记录登录失败"""
    return self.log_event(
      event_type=SecurityEventType.LOGIN_FAILED,
      user_id=user_id,
      ip_address=ip_address,
      success=False,
      message=reason,
      details={"reason": reason}
    )

  def log_password_change(
    self,
    user_id: str,
    success: bool = True,
    reason: Optional[str] = None
  ) -> Dict[str, Any]:
    """记录密码修改"""
    return self.log_event(
      event_type=SecurityEventType.PASSWORD_CHANGE,
      user_id=user_id,
      success=success,
      message=reason,
      details={"reason": reason}
    )

  def log_sql_injection_attempt(
    self,
    ip_address: str,
    query: str,
    user_id: Optional[str] = None
  ) -> Dict[str, Any]:
    """记录 SQL 注入尝试"""
    # 脱敏处理，移除敏感信息
    sanitized_query = query[:200] + "..." if len(query) > 200 else query

    return self.log_event(
      event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
      user_id=user_id,
      ip_address=ip_address,
      success=False,
      message="SQL injection attempt detected",
      details={
        "query_preview": sanitized_query,
        "blocked": True
      }
    )

  def log_sensitive_data_access(
    self,
    user_id: str,
    data_type: str,
    ip_address: Optional[str] = None
  ) -> Dict[str, Any]:
    """记录敏感数据访问"""
    return self.log_event(
      event_type=SecurityEventType.SENSITIVE_DATA_ACCESS,
      user_id=user_id,
      ip_address=ip_address,
      success=True,
      details={"data_type": data_type}
    )

  def log_config_change(
    self,
    user_id: str,
    config_key: str,
    old_value: Any,
    new_value: Any
  ) -> Dict[str, Any]:
    """记录配置变更"""
    return self.log_event(
      event_type=SecurityEventType.CONFIG_CHANGE,
      user_id=user_id,
      success=True,
      details={
        "config_key": config_key,
        "old_value": str(old_value)[:100],
        "new_value": str(new_value)[:100]
      }
    )

  def log_encryption_failure(
    self,
    operation: str,
    error: str,
    user_id: Optional[str] = None
  ) -> Dict[str, Any]:
    """记录加密失败"""
    return self.log_event(
      event_type=SecurityEventType.ENCRYPTION_FAILURE,
      user_id=user_id,
      success=False,
      message=f"Encryption {operation} failed",
      details={
        "operation": operation,
        "error": str(error)[:200]
      }
    )

  def close(self) -> None:
    """关闭日志处理器并释放资源"""
    if hasattr(self, 'file_handler') and self.file_handler:
      self.file_handler.close()
      logger.removeHandler(self.file_handler)


# 创建全局安全审计日志器实例
audit_logger = SecurityAuditLogger()


def get_audit_logger() -> SecurityAuditLogger:
  """
  获取安全审计日志器实例

  Returns:
      SecurityAuditLogger: 安全审计日志器实例
  """
  return audit_logger
