#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阶段3组件单元测试

测试插件系统、Hook管理和Strategy模式。
"""

import pytest
from unittest.mock import MagicMock

from src.infrastructure.plugins import (
  IPlugin,
  PluginInfo,
  PluginState,
  IPluginLoader,
  IPluginLifecycleListener,
)
from src.infrastructure.plugins.plugin_manager import (
  PluginManager,
  PluginLoadResult,
)
from src.infrastructure.hooks import (
  HookManager,
  HookStage,
  HookRegistration,
  registerHook,
  executeHook,
)
from src.infrastructure.strategies import (
  IStrategy,
  StrategyInfo,
  StrategyContext,
  StrategyFactory,
  create_context,
)


class MockPlugin(IPlugin):
  """模拟插件"""

  def __init__(self, name: str = "TestPlugin"):
    self._info = PluginInfo(
      name=name,
      version="1.0.0",
      description="测试插件",
      author="Test"
    )
    self._initialized = False
    self._shutdown = False

  def getInfo(self) -> PluginInfo:
    return self._info

  def initialize(self, context) -> bool:
    self._initialized = True
    return True

  def execute(self, action: str, *args, **kwargs):
    return f"Executed: {action}"

  def shutdown(self):
    self._shutdown = True

  def getDependencies(self) -> list:
    return []

  def validateConfig(self, config) -> tuple:
    return True, ""


class TestPluginInfo:
  """插件信息测试类"""

  def testPluginInfoCreation(self):
    """测试创建插件信息"""
    info = PluginInfo(
      name="TestPlugin",
      version="1.0.0",
      description="测试插件",
      author="Test"
    )
    assert info.name == "TestPlugin"
    assert info.version == "1.0.0"
    assert info.state == PluginState.UNKNOWN

  def testPluginInfoWithDependencies(self):
    """测试带依赖的插件信息"""
    info = PluginInfo(
      name="TestPlugin",
      version="1.0.0",
      description="测试插件",
      author="Test",
      dependencies=["PluginA", "PluginB"]
    )
    assert len(info.dependencies) == 2
    assert "PluginA" in info.dependencies


class TestPluginManager:
  """插件管理器测试类"""

  def testRegisterAndGetPlugin(self):
    """测试注册和获取插件"""
    manager = PluginManager()

    plugin = MockPlugin()
    # 直接注册到内部字典进行测试
    manager._plugins["TestPlugin"] = plugin
    manager._pluginInfo["TestPlugin"] = plugin.getInfo()

    assert manager.getPlugin("TestPlugin") == plugin

  def testGetPluginInfo(self):
    """测试获取插件信息"""
    manager = PluginManager()

    plugin = MockPlugin()
    manager._plugins["TestPlugin"] = plugin
    manager._pluginInfo["TestPlugin"] = plugin.getInfo()

    info = manager.getPluginInfo("TestPlugin")
    assert info.name == "TestPlugin"
    assert info.version == "1.0.0"

  def testExecutePluginAction(self):
    """测试执行插件操作"""
    manager = PluginManager()

    plugin = MockPlugin()
    manager._plugins["TestPlugin"] = plugin
    manager._pluginInfo["TestPlugin"] = plugin.getInfo()

    result = manager.executePluginAction("TestPlugin", "test_action")
    assert result == "Executed: test_action"

  def testGetAllPlugins(self):
    """测试获取所有插件"""
    manager = PluginManager()

    manager._plugins["Plugin1"] = MockPlugin("Plugin1")
    manager._plugins["Plugin2"] = MockPlugin("Plugin2")

    plugins = manager.getAllPlugins()
    assert len(plugins) == 2


class TestHookManager:
  """Hook管理器测试类"""

  def testRegisterHook(self):
    """测试注册钩子"""
    manager = HookManager()

    def callback(ctx):
      return "executed"

    hookId = manager.register("test.hook", callback)
    assert hookId
    assert manager.hasHooks("test.hook")

  def testUnregisterHook(self):
    """测试注销钩子"""
    manager = HookManager()

    def callback(ctx):
      return "executed"

    hookId = manager.register("test.hook", callback)
    result = manager.unregister(hookId)
    assert result
    assert not manager.hasHooks("test.hook")

  def testExecuteHook(self):
    """测试执行钩子"""
    manager = HookManager()

    results = []

    def before_hook(ctx):
      results.append("before")
      ctx.data["before"] = True

    def after_hook(ctx):
      results.append("after")
      ctx.data["after"] = True

    manager.register("test.hook", before_hook, HookStage.BEFORE)
    manager.register("test.hook", after_hook, HookStage.AFTER)

    manager.execute("test.hook", {})

    assert "before" in results
    assert "after" in results

  def testHookPriority(self):
    """测试钩子优先级"""
    manager = HookManager()

    results = []

    def low_priority(ctx):
      results.append("low")

    def high_priority(ctx):
      results.append("high")

    manager.register("test.hook", low_priority, HookStage.BEFORE, priority=0)
    manager.register("test.hook", high_priority, HookStage.BEFORE, priority=100)

    manager.execute("test.hook", {})

    assert results[0] == "high"
    assert results[1] == "low"

  def testConvenienceFunctions(self):
    """测试便捷函数"""
    results = []

    def callback(ctx):
      results.append("executed")

    registerHook("convenience.hook", callback)
    executeHook("convenience.hook", {})

    assert len(results) == 1
    assert results[0] == "executed"

  def testHookCount(self):
    """测试钩子计数"""
    manager = HookManager()

    manager.register("hook1", lambda ctx: None)
    manager.register("hook2", lambda ctx: None)
    manager.register("hook1", lambda ctx: None)

    assert manager.getHookCount() == 3
    assert manager.getHookCount("hook1") == 2
    assert manager.getHookCount("hook2") == 1


class TestStrategyContext:
  """策略上下文测试类"""

  def testRegisterStrategy(self):
    """测试注册策略"""
    context = create_context()

    class TestStrategy(IStrategy):
      def execute(self):
        return "test"

      def getInfo(self):
        return StrategyInfo("test", "测试策略", "1.0.0")

      def validate(self):
        return True

    strategy = TestStrategy()
    context.register(strategy)

    assert context.getStrategy("test") == strategy

  def testSetStrategy(self):
    """测试设置当前策略"""
    context = create_context()

    class StrategyA(IStrategy):
      def execute(self):
        return "A"

      def getInfo(self):
        return StrategyInfo("strategyA", "策略A", "1.0.0")

      def validate(self):
        return True

    class StrategyB(IStrategy):
      def execute(self):
        return "B"

      def getInfo(self):
        return StrategyInfo("strategyB", "策略B", "1.0.0")

      def validate(self):
        return True

    context.register(StrategyA())
    context.register(StrategyB())

    context.setStrategy("strategyA")
    assert context.getCurrentStrategy().execute() == "A"

    context.setStrategy("strategyB")
    assert context.getCurrentStrategy().execute() == "B"

  def testExecuteStrategy(self):
    """测试执行策略"""
    context = create_context()

    class AddStrategy(IStrategy):
      def execute(self, a, b):
        return a + b

      def getInfo(self):
        return StrategyInfo("add", "加法策略", "1.0.0")

      def validate(self, a, b):
        return isinstance(a, (int, float)) and isinstance(b, (int, float))

    context.register(AddStrategy())
    context.setStrategy("add")

    result = context.execute(2, 3)
    assert result == 5

  def testListStrategies(self):
    """测试列出策略"""
    context = create_context()

    class StrategyA(IStrategy):
      def execute(self):
        return "A"

      def getInfo(self):
        return StrategyInfo("a", "策略A", "1.0.0")

      def validate(self):
        return True

    class StrategyB(IStrategy):
      def execute(self):
        return "B"

      def getInfo(self):
        return StrategyInfo("b", "策略B", "1.0.0")

      def validate(self):
        return True

    context.register(StrategyA())
    context.register(StrategyB())

    strategies = context.listStrategies()
    assert len(strategies) == 2
    assert "a" in strategies
    assert "b" in strategies


class TestStrategyFactory:
  """策略工厂测试类"""

  def testRegisterAndCreate(self):
    """测试注册和创建"""
    factory = StrategyFactory()

    class TestStrategy(IStrategy):
      def __init__(self, param):
        self.param = param

      def execute(self):
        return self.param

      def getInfo(self):
        return StrategyInfo("test", "测试", "1.0.0")

      def validate(self):
        return True

    factory.register(TestStrategy, "test")
    strategy = factory.create("test", param="hello")

    assert strategy is not None
    assert strategy.param == "hello"


# 运行测试
if __name__ == "__main__":
  pytest.main([__file__, "-v"])
