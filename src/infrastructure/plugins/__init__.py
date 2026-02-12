#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件接口模块

定义插件系统的核心接口。
所有插件都应该实现这些接口。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum, auto

import sys
import os


class PluginState(Enum):
  """插件状态枚举"""
  UNKNOWN = auto()
  LOADED = auto()
  INSTALLED = auto()
  ENABLED = auto()
  DISABLED = auto()
  ERROR = auto()


@dataclass
class PluginInfo:
  """插件信息"""
  name: str
  version: str
  description: str
  author: str
  state: PluginState = PluginState.UNKNOWN
  dependencies: List[str] = field(default_factory=list)
  permissions: List[str] = field(default_factory=list)
  entryPoint: str = ""
  configSchema: Dict[str, Any] = field(default_factory=dict)


class IPlugin(ABC):
  """插件接口

  所有插件都必须实现此接口。
  """

  @abstractmethod
  def getInfo(self) -> PluginInfo:
    """
    获取插件信息

    Returns:
      PluginInfo: 插件信息
    """
    pass

  @abstractmethod
  def initialize(self, context: Dict[str, Any]) -> bool:
    """
    初始化插件

    Args:
      context: 初始化上下文

    Returns:
      bool: 是否初始化成功
    """
    pass

  @abstractmethod
  def execute(self, action: str, *args, **kwargs) -> Any:
    """
    执行插件功能

    Args:
      action: 操作名称
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 执行结果
    """
    pass

  @abstractmethod
  def shutdown(self) -> None:
    """关闭插件"""
    pass

  @abstractmethod
  def getDependencies(self) -> List[str]:
    """
    获取依赖列表

    Returns:
      List[str]: 依赖的插件名称列表
    """
    pass

  @abstractmethod
  def validateConfig(self, config: Dict[str, Any]) -> tuple:
    """
    验证配置

    Args:
      config: 配置字典

    Returns:
      tuple: (是否有效, 错误信息)
    """
    pass


class IPluginLoader(ABC):
  """插件加载器接口"""

  @abstractmethod
  def canLoad(self, pluginPath: str) -> bool:
    """
    检查是否可以加载插件

    Args:
      pluginPath: 插件路径

    Returns:
      bool: 是否可以加载
    """
    pass

  @abstractmethod
  def load(self, pluginPath: str) -> Optional[IPlugin]:
    """
    加载插件

    Args:
      pluginPath: 插件路径

    Returns:
      Optional[IPlugin]: 加载的插件实例
    """
    pass


class IPluginInstaller(ABC):
  """插件安装器接口"""

  @abstractmethod
  def canInstall(self, pluginPath: str) -> bool:
    """
    检查是否可以安装插件

    Args:
      pluginPath: 插件路径

    Returns:
      bool: 是否可以安装
    """
    pass

  @abstractmethod
  def install(self, pluginPath: str, targetPath: str) -> bool:
    """
    安装插件

    Args:
      pluginPath: 插件源路径
      targetPath: 目标路径

    Returns:
      bool: 是否安装成功
    """
    pass

  @abstractmethod
  def uninstall(self, pluginName: str) -> bool:
    """
    卸载插件

    Args:
      pluginName: 插件名称

    Returns:
      bool: 是否卸载成功
    """
    pass


class IPluginLifecycleListener(ABC):
  """插件生命周期监听器接口"""

  @abstractmethod
  def onPluginLoaded(self, plugin: IPlugin) -> None:
    """
    插件加载时回调

    Args:
      plugin: 插件实例
    """
    pass

  @abstractmethod
  def onPluginEnabled(self, plugin: IPlugin) -> None:
    """
    插件启用时回调

    Args:
      plugin: 插件实例
    """
    pass

  @abstractmethod
  def onPluginDisabled(self, plugin: IPlugin) -> None:
    """
    插件禁用时回调

    Args:
      plugin: 插件实例
    """
    pass

  @abstractmethod
  def onPluginError(self, plugin: IPlugin, error: Exception) -> None:
    """
    插件出错时回调

    Args:
      plugin: 插件实例
      error: 异常
    """
    pass


# 导出所有接口
__all__ = [
  'IPlugin',
  'IPluginLoader',
  'IPluginInstaller',
  'IPluginLifecycleListener',
  'PluginInfo',
  'PluginState',
]
