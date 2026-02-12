#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一配置管理器模块

提供增强的配置管理功能：
- 多环境配置支持（开发/测试/生产）
- 配置验证和类型检查
- 配置变更监听
- 配置热重载
"""

import json
import logging
import os
import shutil
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum

from src.infrastructure.interfaces import IConfigProvider
from src.infrastructure.events import EventBus, Event

logger = logging.getLogger(__name__)


class ConfigEnvironment(Enum):
  """配置环境枚举"""
  DEVELOPMENT = "development"
  TESTING = "testing"
  STAGING = "staging"
  PRODUCTION = "production"


@dataclass
class ConfigSchema:
  """配置模式定义"""
  key: str
  type: Type
  required: bool = False
  default: Any = None
  validator: Callable = None
  description: str = ""


@dataclass
class ConfigChange:
  """配置变更记录"""
  key: str
  oldValue: Any
  newValue: Any
  timestamp: str
  source: str


class UnifiedConfigManager(IConfigProvider):
  """
  统一配置管理器

  提供配置的统一管理，支持多环境、验证和变更监听。
  """

  _instance = None
  _lock = threading.Lock()

  def __init__(
    self,
    configDir: str = "config",
    environment: ConfigEnvironment = ConfigEnvironment.DEVELOPMENT
  ):
    """
    初始化统一配置管理器

    Args:
      configDir: 配置目录
      environment: 当前环境
    """
    self.configDir = configDir
    self.environment = environment
    self._config: Dict[str, Any] = {}
    self._schemas: Dict[str, ConfigSchema] = {}
    self._changeHistory: List[ConfigChange] = []
    self._changeListeners: Dict[str, List[Callable]] = {}
    self._configLock = threading.RLock()
    self._environmentOverrides: Dict[ConfigEnvironment, Dict[str, Any]] = {}
    self._lastReloadTime = 0

    # 事件总线
    self._eventBus = EventBus("config")

    # 加载配置
    self._loadAllConfigs()

  @classmethod
  def getInstance(cls, configDir: str = "config") -> 'UnifiedConfigManager':
    """
    获取单例实例

    Args:
      configDir: 配置目录

    Returns:
      UnifiedConfigManager: 单例实例
    """
    with cls._lock:
      if cls._instance is None:
        cls._instance = cls(configDir)
      return cls._instance

  def registerSchema(self, schema: ConfigSchema) -> None:
    """
    注册配置模式

    Args:
      schema: 配置模式
    """
    with self._configLock:
      self._schemas[schema.key] = schema
      logger.debug(f"已注册配置模式: {schema.key}")

  def registerSchemas(self, schemas: List[ConfigSchema]) -> None:
    """
    批量注册配置模式

    Args:
      schemas: 配置模式列表
    """
    for schema in schemas:
      self.registerSchema(schema)

  def setEnvironment(self, environment: ConfigEnvironment) -> bool:
    """
    设置运行环境

    Args:
      environment: 环境名称

    Returns:
      bool: 是否设置成功
    """
    if environment not in ConfigEnvironment:
      logger.error(f"未知环境: {environment}")
      return False

    oldEnv = self.environment
    self.environment = environment

    # 发布环境变更事件
    self._eventBus.publish(Event("config.environment_changed", {
      "oldEnvironment": oldEnv.value,
      "newEnvironment": environment.value
    }))

    # 重新加载配置
    self.reloadConfig()

    logger.info(f"环境已切换: {oldEnv.value} -> {environment.value}")
    return True

  def getEnvironment(self) -> ConfigEnvironment:
    """
    获取当前环境

    Returns:
      ConfigEnvironment: 当前环境
    """
    return self.environment

  def setEnvironmentOverride(
    self,
    environment: ConfigEnvironment,
    overrides: Dict[str, Any]
  ) -> None:
    """
    设置环境覆盖配置

    Args:
      environment: 环境
      overrides: 覆盖配置
    """
    self._environmentOverrides[environment] = overrides

  def get(self, key: str, default: Any = None) -> Any:
    """
    获取配置值

    实现 IConfigProvider 接口。

    Args:
      key: 配置键（支持点号分隔的嵌套键）
      default: 默认值

    Returns:
      Any: 配置值
    """
    with self._configLock:
      # 逐层查找
      keys = key.split('.')
      value = self._config

      for k in keys:
        if isinstance(value, dict) and k in value:
          value = value[k]
        else:
          return default

      # 检查环境覆盖
      if self.environment in self._environmentOverrides:
        envConfig = self._environmentOverrides[self.environment]
        envValue = envConfig

        for k in keys:
          if isinstance(envValue, dict) and k in envValue:
            envValue = envValue[k]
          else:
            break
        else:
          # 环境覆盖存在且完整
          return envValue

      return value

  def set(self, key: str, value: Any, source: str = "user") -> bool:
    """
    设置配置值

    实现 IConfigProvider 接口。

    Args:
      key: 配置键
      value: 配置值
      source: 设置来源

    Returns:
      bool: 是否设置成功
    """
    # 验证配置
    if not self._validateConfig(key, value):
      logger.error(f"配置验证失败: {key} = {value}")
      return False

    # 记录变更
    oldValue = self.get(key)

    with self._configLock:
      # 逐层设置
      keys = key.split('.')
      config = self._config

      for k in keys[:-1]:
        if k not in config:
          config[k] = {}
        config = config[k]

      config[keys[-1]] = value

    # 记录变更历史
    self._recordChange(key, oldValue, value, source)

    # 通知变更
    self._notifyChange(key, oldValue, value)

    logger.debug(f"配置已设置: {key} = {value}")
    return True

  def load(self) -> bool:
    """
    加载配置

    实现 IConfigProvider 接口。

    Returns:
      bool: 是否加载成功
    """
    return self._loadAllConfigs()

  def save(self) -> bool:
    """
    保存配置

    实现 IConfigProvider 接口。

    Returns:
      bool: 是否保存成功
    """
    return self._saveConfig()

  def reloadConfig(self) -> bool:
    """
    重新加载配置

    Returns:
      bool: 是否加载成功
    """
    result = self._loadAllConfigs()
    if result:
      self._lastReloadTime = time.time()
      # 发布重载事件
      self._eventBus.publish(Event("config.reloaded", {
        "timestamp": self._lastReloadTime
      }))
    return result

  def getAll(self) -> Dict[str, Any]:
    """
    获取所有配置

    Returns:
      Dict[str, Any]: 配置字典
    """
    with self._configLock:
      return dict(self._config)

  def reset(self, source: str = "reset") -> None:
    """
    重置为默认配置

    Args:
      source: 来源
    """
    with self._configLock:
      oldConfig = dict(self._config)
      self._config = {}

    self._recordChange("__all__", oldConfig, {}, source)
    self._notifyChange("__all__", oldConfig, {})

  def validateConfig(self, key: str, value: Any) -> tuple:
    """
    验证配置值

    Args:
      key: 配置键
      value: 配置值

    Returns:
      tuple: (是否有效, 错误信息)
    """
    if key not in self._schemas:
      return True, ""

    schema = self._schemas[key]

    # 类型检查
    if schema.type and not isinstance(value, schema.type):
      return False, f"类型错误: 期望 {schema.type.__name__}, 实际 {type(value).__name__}"

    # 验证器检查
    if schema.validator and not schema.validator(value):
      return False, "验证器检查失败"

    return True, ""

  def _validateConfig(self, key: str, value: Any) -> bool:
    """内部验证配置"""
    isValid, error = self.validateConfig(key, value)
    return isValid

  def _loadAllConfigs(self) -> bool:
    """加载所有配置文件"""
    try:
      with self._configLock:
        # 加载基础配置
        baseConfig = self._loadConfigFile("config.json")
        if baseConfig:
          self._config.update(baseConfig)

        # 加载环境配置
        envConfig = self._loadConfigFile(f"config.{self.environment.value}.json")
        if envConfig:
          # 深度合并环境配置
          self._config = self._deepMerge(self._config, envConfig)

        # 应用环境覆盖
        if self.environment in self._environmentOverrides:
          self._config = self._deepMerge(
            self._config,
            self._environmentOverrides[self.environment]
          )

      logger.info(f"配置已加载 (环境: {self.environment.value})")
      return True

    except Exception as e:
      logger.error(f"加载配置失败: {e}")
      return False

  def _loadConfigFile(self, filename: str) -> Optional[Dict[str, Any]]:
    """
    加载配置文件

    Args:
      filename: 文件名

    Returns:
      Optional[Dict[str, Any]]: 配置字典
    """
    filepath = os.path.join(self.configDir, filename)

    if not os.path.exists(filepath):
      logger.debug(f"配置文件不存在: {filepath}")
      return None

    try:
      with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception as e:
      logger.error(f"加载配置文件失败 {filepath}: {e}")
      return None

  def _saveConfig(self) -> bool:
    """保存配置到文件"""
    try:
      filepath = os.path.join(self.configDir, "config.json")

      with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(self._config, f, ensure_ascii=False, indent=2)

      logger.info(f"配置已保存: {filepath}")
      return True

    except Exception as e:
      logger.error(f"保存配置失败: {e}")
      return False

  def _deepMerge(self, base: Dict, override: Dict) -> Dict:
    """
    深度合并字典

    Args:
      base: 基础字典
      override: 覆盖字典

    Returns:
      Dict: 合并后的字典
    """
    result = dict(base)

    for key, value in override.items():
      if key in result and isinstance(result[key], dict) and isinstance(value, dict):
        result[key] = self._deepMerge(result[key], value)
      else:
        result[key] = value

    return result

  def _recordChange(
    self,
    key: str,
    oldValue: Any,
    newValue: Any,
    source: str
  ) -> None:
    """记录配置变更"""
    change = ConfigChange(
      key=key,
      oldValue=oldValue,
      newValue=newValue,
      timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
      source=source
    )

    self._changeHistory.append(change)

    # 限制历史记录数量
    if len(self._changeHistory) > 1000:
      self._changeHistory = self._changeHistory[-1000:]

  def _notifyChange(self, key: str, oldValue: Any, newValue: Any) -> None:
    """通知配置变更"""
    # 发布事件
    self._eventBus.publish(Event("config.changed", {
      "key": key,
      "oldValue": oldValue,
      "newValue": newValue
    }))

    # 调用监听器
    if key in self._changeListeners:
      for callback in self._changeListeners[key]:
        try:
          callback(key, oldValue, newValue)
        except Exception as e:
          logger.error(f"配置变更监听器执行失败: {e}")

  def addChangeListener(self, key: str, callback: Callable) -> str:
    """
    添加配置变更监听器

    Args:
      key: 配置键
      callback: 回调函数

    Returns:
      str: 监听器ID
    """
    listenerId = str(id(callback))

    if key not in self._changeListeners:
      self._changeListeners[key] = []

    self._changeListeners[key].append(callback)

    return listenerId

  def removeChangeListener(self, listenerId: str) -> bool:
    """
    移除配置变更监听器

    Args:
      listenerId: 监听器ID

    Returns:
      bool: 是否移除成功
    """
    for key, listeners in self._changeListeners.items():
      for callback in listeners:
        if str(id(callback)) == listenerId:
          listeners.remove(callback)
          return True

    return False

  def getChangeHistory(self, key: str = None) -> List[ConfigChange]:
    """
    获取配置变更历史

    Args:
      key: 配置键（可选）

    Returns:
      List[ConfigChange]: 变更历史
    """
    if key:
      return [c for c in self._changeHistory if c.key == key]
    return list(self._changeHistory)

  def exportConfig(self, filepath: str) -> bool:
    """
    导出配置

    Args:
      filepath: 导出路径

    Returns:
      bool: 是否导出成功
    """
    try:
      with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(self._config, f, ensure_ascii=False, indent=2)
      return True
    except Exception as e:
      logger.error(f"导出配置失败: {e}")
      return False

  def importConfig(self, filepath: str, merge: bool = True) -> bool:
    """
    导入配置

    Args:
      filepath: 导入路径
      merge: 是否合并到现有配置

    Returns:
      bool: 是否导入成功
    """
    try:
      with open(filepath, 'r', encoding='utf-8') as f:
        importedConfig = json.load(f)

      with self._configLock:
        if merge:
          self._config = self._deepMerge(self._config, importedConfig)
        else:
          self._config = importedConfig

      # 验证所有配置
      for key in self._schemas:
        if not self._validateConfig(key, self.get(key, None)):
          logger.warning(f"导入的配置验证失败: {key}")

      return True

    except Exception as e:
      logger.error(f"导入配置失败: {e}")
      return False


# 创建默认实例
_defaultConfigManager = None


def getUnifiedConfigManager(configDir: str = "config") -> UnifiedConfigManager:
  """
  获取统一配置管理器实例

  Args:
    configDir: 配置目录

  Returns:
    UnifiedConfigManager: 配置管理器实例
  """
  return UnifiedConfigManager.getInstance(configDir)


# 导出
__all__ = [
  'UnifiedConfigManager',
  'ConfigEnvironment',
  'ConfigSchema',
  'ConfigChange',
  'getUnifiedConfigManager',
]
