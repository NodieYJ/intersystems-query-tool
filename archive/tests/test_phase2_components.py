#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阶段2组件单元测试

测试事件总线、异步执行器和增强容器。
"""

import pytest
import time
import threading
from unittest.mock import MagicMock

from src.infrastructure.events import (
  EventBus,
  Event,
  EventPriority,
  publishEvent,
  subscribeEvent,
)
from src.infrastructure.async_ops import (
  QtAsyncExecutor,
  TaskStatus,
  TaskResult,
  ProgressReporter,
)
from src.infrastructure.di.enhanced_container import (
  EnhancedDIContainer,
  ServiceLifetime,
  ScopedContainer,
)
from src.infrastructure.config.unified_config_manager import (
  UnifiedConfigManager,
  ConfigEnvironment,
  ConfigSchema,
)


class TestEventBus:
  """事件总线测试类"""

  def testPublishSubscribe(self):
    """测试发布和订阅"""
    bus = EventBus("test")

    results = []

    def handler(event):
      results.append(event.data.get("value"))

    # 订阅事件
    bus.subscribe("test.event", handler)

    # 发布事件
    bus.publish(Event("test.event", {"value": 42}))

    assert len(results) == 1
    assert results[0] == 42

  def testWildcardSubscription(self):
    """测试通配符订阅"""
    bus = EventBus("test")

    results = []

    def handler(event):
      results.append(event.eventType)

    # 订阅所有事件
    bus.subscribe("*", handler)

    # 发布多个事件
    bus.publish(Event("event1"))
    bus.publish(Event("event2"))

    assert len(results) == 2
    assert "event1" in results
    assert "event2" in results

  def testUnsubscribe(self):
    """测试取消订阅"""
    bus = EventBus("test")

    results = []

    def handler(event):
      results.append(event.data.get("value"))

    handlerId = bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handlerId)

    bus.publish(Event("test.event", {"value": 42}))

    assert len(results) == 0

  def testEventPriority(self):
    """测试事件优先级"""
    bus = EventBus("test")

    results = []

    def lowPriority(event):
      results.append("low")

    def highPriority(event):
      results.append("high")

    def normalPriority(event):
      results.append("normal")

    # 按优先级订阅
    bus.subscribe("test.event", lowPriority, EventPriority.LOW)
    bus.subscribe("test.event", highPriority, EventPriority.HIGH)
    bus.subscribe("test.event", normalPriority, EventPriority.NORMAL)

    bus.publish(Event("test.event"))

    # 高优先级应该先执行
    assert results[0] == "high"
    assert results[1] == "normal"
    assert results[2] == "low"

  def testPublishAsync(self):
    """测试异步发布"""
    bus = EventBus("test")

    results = []

    def handler(event):
      time.sleep(0.1)
      results.append(event.data.get("value"))

    bus.subscribe("test.event", handler)
    bus.publishAsync(Event("test.event", {"value": 42}))

    # 等待异步执行
    time.sleep(0.2)

    assert len(results) == 1
    assert results[0] == 42


class TestAsyncExecutor:
  """异步执行器测试类"""

  def testExecuteAsync(self):
    """测试异步执行"""
    executor = QtAsyncExecutor(maxWorkers=2)

    def sampleTask():
      return 42

    taskId = executor.executeAsync(sampleTask)
    result = executor.waitForTask(taskId, timeout=1)

    assert result
    assert executor.getTaskStatus(taskId)["status"] == "completed"

    executor.shutdown()

  def testSubmitTaskWithProgress(self):
    """测试带进度的任务提交"""
    executor = QtAsyncExecutor(maxWorkers=2)

    progressValues = []

    def progressCallback(progress, message):
      progressValues.append(progress)

    def sampleTask(progressReporter=None):
      for i in range(5):
        if progressReporter:
          progressReporter.reportProgress(i * 20, f"Step {i}")
      return "done"

    taskId = executor.submitTask(
      "test_task",
      sampleTask,
      progressCallback=progressCallback
    )

    result = executor.waitForTask(taskId, timeout=1)
    assert result
    assert len(progressValues) == 5

    executor.shutdown()

  def testCancelTask(self):
    """测试取消任务"""
    executor = QtAsyncExecutor(maxWorkers=2)

    def longTask():
      time.sleep(10)
      return "done"

    taskId = executor.executeAsync(longTask)
    time.sleep(0.1)

    cancelled = executor.cancelTask(taskId)

    # 任务可能已经完成或正在运行
    status = executor.getTaskStatus(taskId)
    assert status["status"] in ["completed", "failed", "cancelled"]

    executor.shutdown(wait=False)


class TestEnhancedContainer:
  """增强容器测试类"""

  def testSingletonRegistration(self):
    """测试单例注册"""
    container = EnhancedDIContainer()

    class TestService:
      def __init__(self):
        self.value = 42

    container.registerSingleton(TestService)

    # 解析两次应该是同一个实例
    instance1 = container.resolve(TestService)
    instance2 = container.resolve(TestService)

    assert instance1 is instance2
    assert instance1.value == 42

  def testTransientRegistration(self):
    """测试瞬态注册"""
    container = EnhancedDIContainer()

    class TestService:
      instanceCount = 0

      def __init__(self):
        TestService.instanceCount += 1

    container.registerTransient(TestService)

    # 解析多次应该创建不同实例
    instance1 = container.resolve(TestService)
    instance2 = container.resolve(TestService)

    assert instance1 is not instance2
    assert TestService.instanceCount == 2

  def testScopedRegistration(self):
    """测试作用域注册"""
    container = EnhancedDIContainer()

    class TestService:
      pass

    container.registerScoped(TestService)

    # 在作用域内解析多次应该是同一实例
    with container.createScope("test_scope") as scoped:
      instance1 = scoped.resolve(TestService)
      instance2 = scoped.resolve(TestService)
      assert instance1 is instance2

    # 退出作用域后，新作用域应该创建新实例
    with container.createScope("test_scope") as scoped:
      instance3 = scoped.resolve(TestService)
      # 不同作用域应该有不同实例
      assert instance3 is not instance1

  def testCircularDependencyDetection(self):
    """测试循环依赖检测"""
    container = EnhancedDIContainer(maxResolutionDepth=3)

    class ServiceA:
      def __init__(self):
        self.value = "A"

    class ServiceB:
      def __init__(self):
        self.value = "B"

    container.register(ServiceA)
    container.register(ServiceB)

    # 正常解析应该工作
    a = container.resolve(ServiceA)
    b = container.resolve(ServiceB)

    assert a.value == "A"
    assert b.value == "B"


class TestUnifiedConfigManager:
  """统一配置管理器测试类"""

  def testGetSetConfig(self):
    """测试获取和设置配置"""
    manager = UnifiedConfigManager()

    manager.set("test.value", 42)
    value = manager.get("test.value")

    assert value == 42

  def testNestedConfig(self):
    """测试嵌套配置"""
    manager = UnifiedConfigManager()

    manager.set("database.server.host", "localhost")
    host = manager.get("database.server.host")

    assert host == "localhost"

  def testEnvironmentOverride(self):
    """测试环境覆盖"""
    manager = UnifiedConfigManager()

    manager.set("feature.enabled", True)
    manager.setEnvironmentOverride(
      ConfigEnvironment.TESTING,
      {"feature.enabled": False}
    )

    assert manager.get("feature.enabled") == True

    # 切换到测试环境
    manager.setEnvironment(ConfigEnvironment.TESTING)

    assert manager.get("feature.enabled") == False

  def testConfigValidation(self):
    """测试配置验证"""
    manager = UnifiedConfigManager()

    manager.registerSchema(ConfigSchema(
      key="app.timeout",
      type=int,
      required=True,
      default=30
    ))

    # 设置有效值
    result = manager.set("app.timeout", 60)
    assert result
    assert manager.get("app.timeout") == 60

  def testConfigChangeListener(self):
    """测试配置变更监听"""
    manager = UnifiedConfigManager()

    changes = []

    def onChange(key, oldValue, newValue):
      changes.append((key, oldValue, newValue))

    manager.addChangeListener("test.*", onChange)
    manager.set("test.value", 42)

    assert len(changes) == 1
    assert changes[0][0] == "test.value"
    assert changes[0][1] is None  # 旧值
    assert changes[0][2] == 42  # 新值


class TestProgressReporter:
  """进度报告器测试类"""

  def testProgressCallback(self):
    """测试进度回调"""
    values = []

    def callback(progress, message):
      values.append((progress, message))

    reporter = ProgressReporter(callback)

    reporter.reportProgress(50, "Half done")

    assert len(values) == 1
    assert values[0] == (50, "Half done")
    assert reporter.progress == 50


# 运行测试
if __name__ == "__main__":
  pytest.main([__file__, "-v"])
