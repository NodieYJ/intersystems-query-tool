#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DI容器单元测试

测试依赖注入容器的核心功能：
- 服务注册和解析
- 生命周期管理（单例、瞬态、作用域）
- 构造函数自动注入
- 工厂方法注册
- 线程安全性
"""

import sys
import threading
import time
import unittest
from abc import ABC, abstractmethod
from typing import List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, 'D:\\pywindows')

from src.infrastructure.di.container import (
    DIContainer,
    Scope,
    ServiceLifetime,
    get_container,
    configure_services,
)


# ============================================================================
# 测试用的接口和实现类
# ============================================================================

class IService(ABC):
    """测试服务接口"""
    
    @abstractmethod
    def do_something(self) -> str:
        """执行操作"""
        pass


class ServiceImpl(IService):
    """服务实现"""
    
    def __init__(self):
        self.id = id(self)
    
    def do_something(self) -> str:
        return f"Service {self.id}"


class IDependentService(ABC):
    """依赖服务接口"""
    
    @abstractmethod
    def process(self) -> str:
        """处理数据"""
        pass


class DependentServiceImpl(IDependentService):
    """依赖服务实现 - 演示构造函数注入"""
    
    def __init__(self, service: IService):
        self.service = service
    
    def process(self) -> str:
        return f"Processed by {self.service.do_something()}"


class IMultiDependencyService(ABC):
    """多依赖服务接口"""
    pass


class MultiDependencyServiceImpl:
    """多依赖服务实现"""
    
    def __init__(self, service1: IService, service2: IDependentService, optional_param: str = "default"):
        self.service1 = service1
        self.service2 = service2
        self.optional_param = optional_param


class CounterService:
    """计数器服务 - 用于测试生命周期"""
    
    instance_count = 0
    
    def __init__(self):
        CounterService.instance_count += 1
        self.instance_number = CounterService.instance_count


# ============================================================================
# DI容器核心测试
# ============================================================================

class TestDIContainerBasics(unittest.TestCase):
    """DI容器基础功能测试"""
    
    def setUp(self):
        """每个测试前创建新容器"""
        self.container = DIContainer()
    
    def test_register_and_resolve_transient(self):
        """测试瞬态服务注册和解析"""
        # 注册瞬态服务
        self.container.register_transient(IService, ServiceImpl)
        
        # 解析两次，应该得到不同实例
        service1 = self.container.resolve(IService)
        service2 = self.container.resolve(IService)
        
        self.assertIsInstance(service1, ServiceImpl)
        self.assertIsInstance(service2, ServiceImpl)
        self.assertIsNot(service1, service2)  # 瞬态应该不同实例
    
    def test_register_and_resolve_singleton(self):
        """测试单例服务注册和解析"""
        # 注册单例服务
        self.container.register_singleton(IService, ServiceImpl)
        
        # 解析两次，应该得到相同实例
        service1 = self.container.resolve(IService)
        service2 = self.container.resolve(IService)
        
        self.assertIsInstance(service1, ServiceImpl)
        self.assertIs(service1, service2)  # 单例应该相同实例
    
    def test_register_instance(self):
        """测试实例注册"""
        instance = ServiceImpl()
        self.container.register_instance(IService, instance)
        
        resolved = self.container.resolve(IService)
        self.assertIs(resolved, instance)
    
    def test_resolve_unregistered_service(self):
        """测试解析未注册的服务应该抛出异常"""
        with self.assertRaises(KeyError) as context:
            self.container.resolve(IService)
        
        self.assertIn("IService", str(context.exception))
    
    def test_is_registered(self):
        """测试服务注册检查"""
        self.assertFalse(self.container.is_registered(IService))
        
        self.container.register_transient(IService, ServiceImpl)
        self.assertTrue(self.container.is_registered(IService))
    
    def test_get_registered_services(self):
        """测试获取已注册服务列表"""
        self.container.register_transient(IService, ServiceImpl)
        self.container.register_singleton(IDependentService, DependentServiceImpl)
        
        services = self.container.get_registered_services()
        self.assertEqual(len(services), 2)
        self.assertIn("IService", services)
        self.assertIn("IDependentService", services)


class TestDIContainerLifetimes(unittest.TestCase):
    """DI容器生命周期测试"""
    
    def setUp(self):
        """重置计数器并创建新容器"""
        CounterService.instance_count = 0
        self.container = DIContainer()
    
    def test_transient_lifetime(self):
        """测试瞬态生命周期 - 每次解析新实例"""
        self.container.register_transient(CounterService, CounterService)
        
        # 解析3次
        s1 = self.container.resolve(CounterService)
        s2 = self.container.resolve(CounterService)
        s3 = self.container.resolve(CounterService)
        
        # 应该创建3个不同实例
        self.assertEqual(s1.instance_number, 1)
        self.assertEqual(s2.instance_number, 2)
        self.assertEqual(s3.instance_number, 3)
        self.assertIsNot(s1, s2)
        self.assertIsNot(s2, s3)
    
    def test_singleton_lifetime(self):
        """测试单例生命周期 - 全局唯一实例"""
        self.container.register_singleton(CounterService, CounterService)
        
        # 解析3次
        s1 = self.container.resolve(CounterService)
        s2 = self.container.resolve(CounterService)
        s3 = self.container.resolve(CounterService)
        
        # 应该只创建1个实例
        self.assertEqual(s1.instance_number, 1)
        self.assertEqual(s2.instance_number, 1)
        self.assertEqual(s3.instance_number, 1)
        self.assertIs(s1, s2)
        self.assertIs(s2, s3)
    
    def test_scoped_lifetime(self):
        """测试作用域生命周期 - 同一作用域内共享"""
        self.container.register_scoped(CounterService, CounterService)
        
        # 作用域1
        scope1_service1 = self.container.resolve(CounterService, "scope1")
        scope1_service2 = self.container.resolve(CounterService, "scope1")
        
        # 作用域2
        scope2_service1 = self.container.resolve(CounterService, "scope2")
        scope2_service2 = self.container.resolve(CounterService, "scope2")
        
        # 同一作用域内应该相同
        self.assertIs(scope1_service1, scope1_service2)
        self.assertIs(scope2_service1, scope2_service2)
        
        # 不同作用域应该不同
        self.assertIsNot(scope1_service1, scope2_service1)
    
    def test_scoped_requires_scope_id(self):
        """测试作用域服务必须提供scope_id"""
        self.container.register_scoped(CounterService, CounterService)
        
        with self.assertRaises(ValueError) as context:
            self.container.resolve(CounterService)  # 不提供scope_id
        
        self.assertIn("scope_id", str(context.exception))


class TestDIContainerAutoInjection(unittest.TestCase):
    """DI容器自动注入测试"""
    
    def setUp(self):
        """创建新容器并注册基础服务"""
        self.container = DIContainer()
        self.container.register_singleton(IService, ServiceImpl)
    
    def test_constructor_injection(self):
        """测试构造函数自动注入"""
        self.container.register_transient(IDependentService, DependentServiceImpl)
        
        # 解析依赖服务，应该自动注入IService
        dependent = self.container.resolve(IDependentService)
        
        self.assertIsInstance(dependent, DependentServiceImpl)
        self.assertIsInstance(dependent.service, ServiceImpl)
        self.assertEqual(dependent.process(), f"Processed by Service {dependent.service.id}")
    
    def test_multi_dependency_injection(self):
        """测试多依赖注入"""
        self.container.register_transient(IDependentService, DependentServiceImpl)
        self.container.register_transient(IMultiDependencyService, MultiDependencyServiceImpl)
        
        # 解析多依赖服务
        multi = self.container.resolve(IMultiDependencyService)
        
        self.assertIsInstance(multi.service1, ServiceImpl)
        self.assertIsInstance(multi.service2, DependentServiceImpl)
        self.assertEqual(multi.optional_param, "default")  # 默认值保留


class TestDIContainerFactory(unittest.TestCase):
    """DI容器工厂方法测试"""
    
    def setUp(self):
        self.container = DIContainer()
    
    def test_factory_registration(self):
        """测试工厂方法注册"""
        call_count = [0]
        
        def factory():
            call_count[0] += 1
            return ServiceImpl()
        
        self.container.register_factory(IService, factory, ServiceLifetime.TRANSIENT)
        
        # 解析两次
        s1 = self.container.resolve(IService)
        s2 = self.container.resolve(IService)
        
        # 工厂应该被调用两次
        self.assertEqual(call_count[0], 2)
        self.assertIsInstance(s1, ServiceImpl)
        self.assertIsInstance(s2, ServiceImpl)
    
    def test_singleton_factory(self):
        """测试单例工厂"""
        call_count = [0]
        
        def factory():
            call_count[0] += 1
            return ServiceImpl()
        
        self.container.register_factory(IService, factory, ServiceLifetime.SINGLETON)
        
        # 解析3次
        s1 = self.container.resolve(IService)
        s2 = self.container.resolve(IService)
        s3 = self.container.resolve(IService)
        
        # 工厂应该只被调用1次
        self.assertEqual(call_count[0], 1)
        self.assertIs(s1, s2)
        self.assertIs(s2, s3)


class TestDIContainerScope(unittest.TestCase):
    """DI容器作用域测试"""
    
    def setUp(self):
        self.container = DIContainer()
        self.container.register_scoped(CounterService, CounterService)
    
    def test_scope_context_manager(self):
        """测试作用域上下文管理器"""
        with self.container.create_scope("test_scope") as scope:
            # 在作用域内解析
            s1 = scope.resolve(CounterService)
            s2 = scope.resolve(CounterService)
            
            # 同一作用域内应该相同
            self.assertIs(s1, s2)
        
        # 作用域结束后应该能创建新作用域
        with self.container.create_scope("new_scope") as new_scope:
            s3 = new_scope.resolve(CounterService)
            self.assertIsNot(s3, s1)
    
    def test_scope_dispose(self):
        """测试作用域销毁"""
        scope = self.container.create_scope("dispose_test")
        
        # 解析服务
        s1 = scope.resolve(CounterService)
        
        # 销毁作用域
        scope.dispose()
        
        # 再次解析应该失败（作用域已销毁）
        with self.assertRaises(RuntimeError) as context:
            scope.resolve(CounterService)
        
        self.assertIn("销毁", str(context.exception))


class TestDIContainerThreadSafety(unittest.TestCase):
    """DI容器线程安全测试"""
    
    def setUp(self):
        self.container = DIContainer()
        self.container.register_singleton(CounterService, CounterService)
        self.instances: List[CounterService] = []
        self.lock = threading.Lock()
    
    def test_singleton_thread_safety(self):
        """测试单例的线程安全性"""
        def resolve_service():
            service = self.container.resolve(CounterService)
            with self.lock:
                self.instances.append(service)
        
        # 创建多个线程同时解析
        threads = []
        for _ in range(10):
            t = threading.Thread(target=resolve_service)
            threads.append(t)
        
        # 启动所有线程
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 所有实例应该相同（单例）
        first_instance = self.instances[0]
        for instance in self.instances[1:]:
            self.assertIs(instance, first_instance)


class TestGlobalContainer(unittest.TestCase):
    """全局容器测试"""
    
    def test_get_container_singleton(self):
        """测试get_container返回单例"""
        container1 = get_container()
        container2 = get_container()
        
        self.assertIs(container1, container2)
    
    def test_configure_services(self):
        """测试配置服务函数"""
        configured = [False]
        
        def configure(container):
            container.register_transient(IService, ServiceImpl)
            configured[0] = True
        
        container = configure_services(configure)
        
        self.assertTrue(configured[0])
        self.assertTrue(container.is_registered(IService))


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainerBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainerLifetimes))
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainerAutoInjection))
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainerFactory))
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainerScope))
    suite.addTests(loader.loadTestsFromTestCase(TestDIContainerThreadSafety))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalContainer))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)
