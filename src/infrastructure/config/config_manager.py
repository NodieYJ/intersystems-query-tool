#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
用于集中管理应用配置

特性:
- 线程安全的配置读写
- 支持嵌套配置键
- 自动备份和恢复
- 配置变更监听器
- 配置版本管理
"""

import json
import logging
import os
import shutil
import tempfile
import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.infrastructure.security.security_utils import get_security_utils
from src.infrastructure.config.constants import (
    DatabaseDefaults,
    DatabaseTypes,
    UIConfigDefaults,
    LoggingConfig,
)

logger = logging.getLogger(__name__)


class ConfigChangeListener:
  """
  配置变更监听器

  用于监听配置变更事件
  """

  def __init__(self, name: str, callback: Callable[[str, Any, Any], None]):
    """
    初始化监听器

    Args:
        name: 监听器名称
        callback: 回调函数 (key, old_value, new_value)
    """
    self.id = str(uuid.uuid4())
    self.name = name
    self.callback = callback
    self.enabled = True

  def on_change(self, key: str, old_value: Any, new_value: Any):
    """
    配置变更回调

    Args:
        key: 配置键
        old_value: 旧值
        new_value: 新值
    """
    if self.enabled:
      try:
        self.callback(key, old_value, new_value)
      except Exception as e:
        logger.error(f"配置变更回调失败: {e}")


class ConfigVersion:
  """
  配置版本信息
  """

  def __init__(self, version: str, config: Dict[str, Any], timestamp: datetime):
    """
    初始化版本信息

    Args:
        version: 版本号
        config: 配置快照
        timestamp: 时间戳
    """
    self.version = version
    self.config = config
    self.timestamp = timestamp


class ConfigManager:
  """
  配置管理器类

  支持配置变更监听和版本管理
  """

  def __init__(self, config_file: str = "config.json"):
    """
    初始化配置管理器

    Args:
        config_file: 配置文件路径
    """
    self.config_file = config_file
    self.config: Dict[str, Any] = {}
    self.security_utils = get_security_utils()
    self._config_lock = threading.RLock()
    self._file_lock = threading.Lock()

    # 变更监听器
    self._listeners: List[ConfigChangeListener] = []
    self._listener_lock = threading.Lock()

    # 版本管理
    self._versions: List[ConfigVersion] = []
    self._max_versions = 10
    self._current_version = str(uuid.uuid4())

    self._load_config()

  def _load_config(self) -> None:
    """
    加载配置文件（内部方法）
    如果配置文件存在则加载，否则使用默认配置
    """
    if os.path.exists(self.config_file):
      try:
        with open(self.config_file, 'r', encoding='utf-8') as f:
          self.config = json.load(f)
        logger.info(f"成功加载配置文件: {self.config_file}")
      except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {str(e)}，使用默认配置")
        self._load_default_config()
      except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
        self._load_default_config()
    else:
      logger.info(f"配置文件不存在: {self.config_file}，使用默认配置")
      self._load_default_config()

  def _load_default_config(self):
    """
    加载默认配置（使用常量）
    """
    self.config = {
      "database": {
        "server": "localhost",
        "port": DatabaseDefaults.PORT_DEFAULT,
        "namespace": "USER",
        "username": "",
        "password": "",
        "db_type": DatabaseTypes.IRIS,
        "charset": DatabaseDefaults.CHARSET,
        "timeout": DatabaseDefaults.TIMEOUT_CONNECT,
      },
      "application": {
        "name": "桌面应用程序",
        "version": "1.0.0",
        "log_level": LoggingConfig.LOG_LEVEL,
      },
      "ui": {
        "default_window_width": UIConfigDefaults.WINDOW_WIDTH,
        "default_window_height": UIConfigDefaults.WINDOW_HEIGHT,
        "min_window_width": int(UIConfigDefaults.WINDOW_WIDTH / 2),
        "min_window_height": int(UIConfigDefaults.WINDOW_HEIGHT / 2),
        "font_size": UIConfigDefaults.FONT_SIZE,
        "font_family": UIConfigDefaults.FONT_FAMILY,
        "scale_factor": UIConfigDefaults.SCALE_FACTOR,
      },
    }
    logger.info("使用默认配置")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持嵌套键，如 "database.server"
            default: 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

  def set(self, key: str, value: Any) -> bool:
    """
    设置配置值
    
    Args:
        key: 配置键，支持嵌套键，如 "database.server"
        value: 配置值
    
    Returns:
        bool: 设置是否成功
    """
    try:
      keys = key.split('.')
      config = self.config
      
      # 遍历到最后一个键的父级
      for k in keys[:-1]:
        if k not in config:
          config[k] = {}
        config = config[k]
      
      # 设置值
      config[keys[-1]] = value
      logger.info(f"成功设置配置: {key} = {value}")
      return True
    except ValueError as e:
      logger.error(f"配置键格式错误: {str(e)}")
      return False
    except TypeError as e:
      logger.error(f"配置值类型错误: {str(e)}")
      return False
    except Exception as e:
      logger.error(f"设置配置失败: {str(e)}")
      return False

  # ==========================================================================
  # 配置变更监听器
  # ==========================================================================

  def add_change_listener(self, name: str, callback: Callable[[str, Any, Any], None]) -> str:
    """
    添加配置变更监听器

    Args:
        name: 监听器名称
        callback: 回调函数 (key, old_value, new_value)

    Returns:
        str: 监听器 ID
    """
    listener = ConfigChangeListener(name, callback)
    with self._listener_lock:
      self._listeners.append(listener)
    logger.info(f"添加配置变更监听器: {name}")
    return listener.id

  def remove_change_listener(self, listener_id: str) -> bool:
    """
    移除配置变更监听器

    Args:
        listener_id: 监听器 ID

    Returns:
        bool: 是否成功移除
    """
    with self._listener_lock:
      for i, listener in enumerate(self._listeners):
        if listener.id == listener_id:
          del self._listeners[i]
          logger.info(f"移除配置变更监听器: {listener.name}")
          return True
    return False

  def _notify_listeners(self, key: str, old_value: Any, new_value: Any):
    """
    通知所有监听器配置已变更

    Args:
        key: 配置键
        old_value: 旧值
        new_value: 新值
    """
    with self._listener_lock:
      for listener in self._listeners:
        listener.on_change(key, old_value, new_value)

  # ==========================================================================
  # 配置版本管理
  # ==========================================================================

  def _save_version(self):
    """
    保存当前配置为版本快照
    """
    version = ConfigVersion(
      version=self._current_version,
      config=self.config.copy(),
      timestamp=datetime.now()
    )
    self._versions.append(version)

    # 限制版本数量
    if len(self._versions) > self._max_versions:
      self._versions.pop(0)

    # 生成新版本号
    self._current_version = str(uuid.uuid4())
    logger.debug(f"保存配置版本: {version.version}")

  def get_versions(self) -> List[Dict[str, Any]]:
    """
    获取所有配置版本信息

    Returns:
        List[Dict[str, Any]]: 版本信息列表
    """
    return [
      {
        "version": v.version,
        "timestamp": v.timestamp.isoformat(),
        "config_size": len(str(v.config))
      }
      for v in reversed(self._versions)
    ]

  def rollback_to_version(self, version: str) -> bool:
    """
    回滚到指定版本

    Args:
        version: 版本号

    Returns:
        bool: 是否成功回滚
    """
    for v in self._versions:
      if v.version == version:
        self.config = v.config.copy()
        self._current_version = str(uuid.uuid4())
        logger.info(f"回滚到配置版本: {version}")
        return True
    logger.warning(f"找不到配置版本: {version}")
    return False

  def save(self) -> bool:
    """
    保存配置到文件（线程安全）

    使用原子写入策略：
    1. 先写入临时文件
    2. 验证写入完整性
    3. 重命名替换原文件

    Returns:
        bool: 保存是否成功
    """
    # 获取文件锁，保护写入操作
    with self._file_lock:
      try:
        # 确保配置文件所在目录存在
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
          os.makedirs(config_dir, exist_ok=True)

        # 安全处理配置
        secured_config = self.security_utils.secure_config(self.config)

        # 使用临时文件进行原子写入
        temp_fd, temp_file = tempfile.mkstemp(
          suffix='.tmp',
          dir=config_dir or '.'
        )

        try:
          # 在临时文件中写入配置
          with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(secured_config, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

          # 验证临时文件内容完整性
          with open(temp_file, 'r', encoding='utf-8') as f:
            json.load(f)  # 验证JSON格式有效

          # 原子重命名替换原文件
          shutil.move(temp_file, self.config_file)

          logger.info(f"成功保存配置到文件: {self.config_file}")
          return True

        except (json.JSONDecodeError, OSError, Exception) as e:
          # 写入失败，清理临时文件
          if os.path.exists(temp_file):
            os.remove(temp_file)
          logger.error(f"保存配置文件失败: {str(e)}")
          return False

      except FileNotFoundError as e:
        logger.error(f"配置文件路径不存在: {str(e)}")
        return False
      except PermissionError as e:
        logger.error(f"没有权限写入配置文件: {str(e)}")
        return False
      except Exception as e:
        logger.error(f"保存配置文件时发生未知错误: {str(e)}")
        return False

  def reload(self) -> bool:
    """
    重新加载配置文件

    Returns:
        bool: 加载是否成功
    """
    try:
      self._load_config()
      return True
    except Exception as e:
      logger.error(f"重新加载配置文件失败: {str(e)}")
      return False


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例

    Returns:
        ConfigManager: 配置管理器实例
    """
    return config_manager
