#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件管理器模块

提供插件的加载、卸载、启用和禁用功能。
支持插件生命周期管理和依赖解析。
"""

import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum

from src.infrastructure.plugins import (
  IPlugin,
  IPluginLoader,
  IPluginLifecycleListener,
  PluginInfo,
  PluginState,
)

logger = logging.getLogger(__name__)


@dataclass
class PluginLoadResult:
  """插件加载结果"""
  success: bool
  plugin: Optional[IPlugin] = None
  error: Optional[str] = None
  loadTime: float = 0.0


class PluginManager:
  """
  插件管理器

  管理应用程序的所有插件。
  支持插件的加载、卸载、启用、禁用和依赖解析。
  """

  _instance = None
  _lock = None

  def __init__(self):
    """初始化插件管理器"""
    self._plugins: Dict[str, IPlugin] = {}
    self._pluginInfo: Dict[str, PluginInfo] = {}
    self._loaders: List[IPluginLoader] = []
    self._listeners: List[IPluginLifecycleListener] = []
    self._pluginPath: str = "plugins"
    self._lock = logging.getLogger(__name__).handlers[0] if logging.getLogger(__name__).handlers else None

    # 自动注册默认加载器
    self._registerDefaultLoaders()

  @classmethod
  def getInstance(cls) -> 'PluginManager':
    """获取单例实例"""
    if cls._instance is None:
      cls._instance = cls()
    return cls._instance

  def _registerDefaultLoaders(self):
    """注册默认加载器"""
    # Python模块加载器
    class PythonModuleLoader(IPluginLoader):
      """Python模块插件加载器"""

      def canLoad(self, pluginPath: str) -> bool:
        path = Path(pluginPath)
        return path.exists() and (path / "__init__.py").exists()

      def load(self, pluginPath: str) -> Optional[IPlugin]:
        try:
          # 添加到路径
          sys.path.insert(0, pluginPath)

          # 导入模块
          moduleName = Path(pluginPath).name
          spec = importlib.util.spec_from_file_location(
            moduleName,
            Path(pluginPath) / "__init__.py"
          )

          if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[moduleName] = module
            spec.loader.exec_module(module)

            # 查找插件类
            for attrName in dir(module):
              attr = getattr(module, attrName)
              if (
                isinstance(attr, type)
                and issubclass(attr, IPlugin)
                and attr != IPlugin
              ):
                return attr()

          return None

        except Exception as e:
          logger.error(f"加载插件失败: {pluginPath}, 错误: {e}")
          return None

    self._loaders.append(PythonModuleLoader())

    # 配置文件加载器
    class ConfigLoader(IPluginLoader):
      """配置文件插件加载器"""

      def canLoad(self, pluginPath: str) -> bool:
        return Path(pluginPath).with_suffix(".json").exists()

      def load(self, pluginPath: str) -> Optional[IPlugin]:
        import json

        configPath = Path(pluginPath).with_suffix(".json")

        if not configPath.exists():
          return None

        try:
          config = json.loads(configPath.read_text(encoding='utf-8'))

          # 返回基于配置的简单插件
          class ConfigBasedPlugin(IPlugin):
            """基于配置的插件"""

            def __init__(self, config):
              self._config = config
              self._info = PluginInfo(
                name=config.get('name', 'Unknown'),
                version=config.get('version', '1.0.0'),
                description=config.get('description', ''),
                author=config.get('author', 'Unknown')
              )

            def getInfo(self) -> PluginInfo:
              return self._info

            def initialize(self, context: Dict[str, Any]) -> bool:
              return True

            def execute(self, action: str, *args, **kwargs) -> Any:
              return None

            def shutdown(self):
              pass

            def getDependencies(self) -> List[str]:
              return self._config.get('dependencies', [])

            def validateConfig(self, config: Dict[str, Any]) -> tuple:
              return True, ""

          return ConfigBasedPlugin(config)

        except Exception as e:
          logger.error(f"加载配置文件插件失败: {pluginPath}, 错误: {e}")
          return None

    self._loaders.append(ConfigLoader())

  def setPluginPath(self, path: str):
    """
    设置插件路径

    Args:
      path: 插件目录路径
    """
    self._pluginPath = path
    logger.info(f"插件路径已设置为: {path}")

  def registerLoader(self, loader: IPluginLoader):
    """
    注册插件加载器

    Args:
      loader: 加载器实例
    """
    self._loaders.append(loader)
    logger.debug(f"已注册插件加载器: {loader.__class__.__name__}")

  def addLifecycleListener(self, listener: IPluginLifecycleListener):
    """
    添加生命周期监听器

    Args:
      listener: 监听器实例
    """
    self._listeners.append(listener)

  def discoverPlugins(self) -> List[str]:
    """
    发现插件目录中的所有插件

    Returns:
      List[str]: 发现的插件路径列表
    """
    plugins = []
    pluginDir = Path(self._pluginPath)

    if not pluginDir.exists():
      logger.warning(f"插件目录不存在: {pluginDir}")
      return plugins

    for item in pluginDir.iterdir():
      if item.is_dir() and (item / "__init__.py").exists():
        plugins.append(str(item))
      elif item.suffix == ".json":
        plugins.append(str(item.with_suffix("")))

    logger.info(f"发现 {len(plugins)} 个插件")
    return plugins

  def loadPlugin(self, pluginPath: str) -> PluginLoadResult:
    """
    加载插件

    Args:
      pluginPath: 插件路径

    Returns:
      PluginLoadResult: 加载结果
    """
    import time
    startTime = time.time()

    # 检查是否已加载
    pluginName = Path(pluginPath).name
    if pluginName in self._plugins:
      logger.warning(f"插件已加载: {pluginName}")
      return PluginLoadResult(
        success=True,
        plugin=self._plugins[pluginName]
      )

    # 查找合适的加载器
    for loader in self._loaders:
      if loader.canLoad(pluginPath):
        try:
          plugin = loader.load(pluginPath)

          if plugin:
            # 获取插件信息
            info = plugin.getInfo()
            info.name = pluginName
            self._plugins[pluginName] = plugin
            self._pluginInfo[pluginName] = info

            # 通知监听器
            self._notifyLoaded(plugin)

            loadTime = time.time() - startTime
            logger.info(f"插件已加载: {info.name} v{info.version} ({loadTime:.2f}s)")

            return PluginLoadResult(
              success=True,
              plugin=plugin,
              loadTime=loadTime
            )

        except Exception as e:
          logger.error(f"加载插件失败: {pluginPath}, 错误: {e}")
          return PluginLoadResult(
            success=False,
            error=str(e),
            loadTime=time.time() - startTime
          )

    logger.warning(f"没有找到合适的加载器: {pluginPath}")
    return PluginLoadResult(
      success=False,
      error="No suitable loader found"
    )

  def loadAllPlugins(self, order: str = "topological") -> List[PluginLoadResult]:
    """
    加载所有发现的插件

    Args:
      order: 加载顺序 ("topological" 或 "discovery")

    Returns:
      List[PluginLoadResult]: 加载结果列表
    """
    plugins = self.discoverPlugins()

    if order == "topological":
      plugins = self._sortByDependencies(plugins)

    results = []
    for pluginPath in plugins:
      result = self.loadPlugin(pluginPath)
      results.append(result)

    return results

  def _sortByDependencies(self, plugins: List[str]) -> List[str]:
    """
    按依赖关系排序插件

    Args:
      plugins: 插件路径列表

    Returns:
      List[str]: 排序后的插件路径列表
    """
    # 简化实现：按依赖数量排序（少依赖的先加载）
    def getDependencyCount(path):
      pluginName = Path(path).name
      if pluginName in self._plugins:
        return len(self._plugins[pluginName].getDependencies())
      return 0

    return sorted(plugins, key=getDependencyCount)

  def enablePlugin(self, pluginName: str) -> bool:
    """
    启用插件

    Args:
      pluginName: 插件名称

    Returns:
      bool: 是否启用成功
    """
    if pluginName not in self._pluginInfo:
      logger.error(f"插件不存在: {pluginName}")
      return False

    info = self._pluginInfo[pluginName]

    # 检查依赖
    for dep in info.dependencies:
      if dep not in self._plugins:
        logger.error(f"插件依赖不存在: {dep}")
        return False

      if self._pluginInfo[dep].state != PluginState.ENABLED:
        logger.error(f"依赖插件未启用: {dep}")
        return False

    # 初始化插件
    plugin = self._plugins[pluginName]
    if plugin.initialize({}):
      info.state = PluginState.ENABLED
      self._notifyEnabled(plugin)
      logger.info(f"插件已启用: {pluginName}")
      return True

    logger.error(f"插件初始化失败: {pluginName}")
    return False

  def disablePlugin(self, pluginName: str) -> bool:
    """
    禁用插件

    Args:
      pluginName: 插件名称

    Returns:
      bool: 是否禁用成功
    """
    if pluginName not in self._pluginInfo:
      return False

    info = self._pluginInfo[pluginName]
    plugin = self._plugins[pluginName]

    # 检查是否有其他插件依赖此插件
    for name, otherInfo in self._pluginInfo.items():
      if otherInfo.state == PluginState.ENABLED:
        plugin = self._plugins[name]
        if pluginName in plugin.getDependencies():
          logger.error(f"插件被其他插件依赖: {name}")
          return False

    # 关闭插件
    plugin.shutdown()
    info.state = PluginState.DISABLED
    self._notifyDisabled(plugin)
    logger.info(f"插件已禁用: {pluginName}")
    return True

  def unloadPlugin(self, pluginName: str) -> bool:
    """
    卸载插件

    Args:
      pluginName: 插件名称

    Returns:
      bool: 是否卸载成功
    """
    if pluginName not in self._plugins:
      return False

    plugin = self._plugins[pluginName]

    # 如果已启用，先禁用
    if self._pluginInfo[pluginName].state == PluginState.ENABLED:
      self.disablePlugin(pluginName)

    # 关闭插件
    plugin.shutdown()

    # 移除
    del self._plugins[pluginName]
    del self._pluginInfo[pluginName]

    logger.info(f"插件已卸载: {pluginName}")
    return True

  def getPlugin(self, pluginName: str) -> Optional[IPlugin]:
    """
    获取插件实例

    Args:
      pluginName: 插件名称

    Returns:
      Optional[IPlugin]: 插件实例
    """
    return self._plugins.get(pluginName)

  def getPluginInfo(self, pluginName: str) -> Optional[PluginInfo]:
    """
    获取插件信息

    Args:
      pluginName: 插件名称

    Returns:
      Optional[PluginInfo]: 插件信息
    """
    return self._pluginInfo.get(pluginName)

  def getAllPlugins(self) -> List[PluginInfo]:
    """
    获取所有插件信息

    Returns:
      List[PluginInfo]: 插件信息列表
    """
    return list(self._pluginInfo.values())

  def executePluginAction(
    self,
    pluginName: str,
    action: str,
    *args,
    **kwargs
  ) -> Any:
    """
    执行插件操作

    Args:
      pluginName: 插件名称
      action: 操作名称
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Any: 操作结果
    """
    plugin = self._plugins.get(pluginName)

    if not plugin:
      logger.error(f"插件不存在: {pluginName}")
      return None

    return plugin.execute(action, *args, **kwargs)

  def executeAllPlugins(self, action: str, *args, **kwargs) -> Dict[str, Any]:
    """
    在所有启用的插件上执行操作

    Args:
      action: 操作名称
      *args: 位置参数
      **kwargs: 关键字参数

    Returns:
      Dict[str, Any]: 各插件的执行结果
    """
    results = {}

    for name, info in self._pluginInfo.items():
      if info.state == PluginState.ENABLED:
        try:
          results[name] = self._plugins[name].execute(action, *args, **kwargs)
        except Exception as e:
          results[name] = e

    return results

  def _notifyLoaded(self, plugin: IPlugin):
    """通知插件已加载"""
    for listener in self._listeners:
      try:
        listener.onPluginLoaded(plugin)
      except Exception as e:
        logger.error(f"通知加载失败: {e}")

  def _notifyEnabled(self, plugin: IPlugin):
    """通知插件已启用"""
    for listener in self._listeners:
      try:
        listener.onPluginEnabled(plugin)
      except Exception as e:
        logger.error(f"通知启用失败: {e}")

  def _notifyDisabled(self, plugin: IPlugin):
    """通知插件已禁用"""
    for listener in self._listeners:
      try:
        listener.onPluginDisabled(plugin)
      except Exception as e:
        logger.error(f"通知禁用失败: {e}")

  def shutdown(self):
    """关闭所有插件"""
    for name in list(self._plugins.keys()):
      self.unloadPlugin(name)
    logger.info("所有插件已关闭")


# 创建默认管理器实例
_defaultPluginManager = None


def getPluginManager() -> PluginManager:
  """
  获取插件管理器实例

  Returns:
    PluginManager: 插件管理器实例
  """
  global _defaultPluginManager

  if _defaultPluginManager is None:
    _defaultPluginManager = PluginManager.getInstance()

  return _defaultPluginManager


# 导出
__all__ = [
  'PluginManager',
  'PluginLoadResult',
  'getPluginManager',
]
