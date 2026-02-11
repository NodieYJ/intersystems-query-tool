#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
依赖注入容器模块

提供轻量级的依赖注入容器，用于管理应用程序的组件依赖关系。
支持单例、瞬态和作用域生命周期管理。

使用示例:
    # 创建容器
    container = DIContainer()
    
    # 注册服务
    container.register_singleton(ConfigInterface, UIConfig)
    container.register_singleton(ScalingManagerInterface, ScalingManager)
    
    # 解析服务
    config = container.resolve(ConfigInterface)
    scaling = container.resolve(ScalingManagerInterface)
"""

import inspect
import logging
import sys
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, get_type_hints

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime:
    """服务生命周期枚举"""
    SINGLETON = "singleton"      # 单例 - 全局唯一实例
    TRANSIENT = "transient"      # 瞬态 - 每次解析创建新实例
    SCOPED = "scoped"            # 作用域 - 同一作用域内共享实例


@dataclass
class ServiceDescriptor:
    """服务描述符"""
    interface: Type
    implementation: Union[Type, Callable]
    lifetime: str = ServiceLifetime.TRANSIENT
    instance: Optional[Any] = None
    factory: Optional[Callable] = None


class DIContainer:
    """
    依赖注入容器
    
    管理服务的注册和解析，支持：
    - 接口到实现的映射
    - 三种生命周期（单例、瞬态、作用域）
    - 构造函数自动注入
    - 工厂方法注册
    
    线程安全，可在多线程环境下使用。
    """
    
    def __init__(self):
        """初始化容器"""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scopes: Dict[str, Dict[Type, Any]] = {}
        self._lock = threading.RLock()
        self._resolution_stack: List[Type] = []  # 用于循环依赖检测
        
        logger.debug("DIContainer 初始化完成")
    
    def register(
        self,
        interface: Type[T],
        implementation: Union[Type, Callable],
        lifetime: str = ServiceLifetime.TRANSIENT
    ) -> 'DIContainer':
        """
        注册服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类或工厂函数
            lifetime: 生命周期（singleton/transient/scoped）
            
        Returns:
            DIContainer: 支持链式调用
            
        Example:
            container.register(
                IConfig,
                UIConfig,
                ServiceLifetime.SINGLETON
            )
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=implementation,
                lifetime=lifetime
            )
            self._services[interface] = descriptor
            
            logger.debug(f"注册服务: {interface.__name__} -> {implementation.__name__ if hasattr(implementation, '__name__') else 'factory'}")
            
        return self
    
    def register_singleton(
        self,
        interface: Type[T],
        implementation: Union[Type, Callable]
    ) -> 'DIContainer':
        """
        注册单例服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类或工厂函数
            
        Returns:
            DIContainer: 支持链式调用
        """
        return self.register(interface, implementation, ServiceLifetime.SINGLETON)
    
    def register_transient(
        self,
        interface: Type[T],
        implementation: Union[Type, Callable]
    ) -> 'DIContainer':
        """
        注册瞬态服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类或工厂函数
            
        Returns:
            DIContainer: 支持链式调用
        """
        return self.register(interface, implementation, ServiceLifetime.TRANSIENT)
    
    def register_scoped(
        self,
        interface: Type[T],
        implementation: Union[Type, Callable]
    ) -> 'DIContainer':
        """
        注册作用域服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类或工厂函数
            
        Returns:
            DIContainer: 支持链式调用
        """
        return self.register(interface, implementation, ServiceLifetime.SCOPED)
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """
        注册已有实例（单例）
        
        Args:
            interface: 服务接口类型
            instance: 实例对象
            
        Returns:
            DIContainer: 支持链式调用
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=type(instance),
                lifetime=ServiceLifetime.SINGLETON,
                instance=instance
            )
            self._services[interface] = descriptor
            self._singletons[interface] = instance
            
            logger.debug(f"注册实例: {interface.__name__}")
            
        return self
    
    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[..., T],
        lifetime: str = ServiceLifetime.TRANSIENT
    ) -> 'DIContainer':
        """
        注册工厂方法
        
        Args:
            interface: 服务接口类型
            factory: 工厂函数
            lifetime: 生命周期
            
        Returns:
            DIContainer: 支持链式调用
        """
        with self._lock:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=factory,
                lifetime=lifetime,
                factory=factory
            )
            self._services[interface] = descriptor
            
            logger.debug(f"注册工厂: {interface.__name__}")
            
        return self
    
    def resolve(self, interface: Type[T], scope_id: Optional[str] = None) -> T:
        """
        解析服务（带循环依赖检测）

        Args:
            interface: 服务接口类型
            scope_id: 作用域ID（用于作用域生命周期）

        Returns:
            T: 服务实例

        Raises:
            KeyError: 服务未注册
            RuntimeError: 检测到循环依赖
        """
        # 检查循环依赖（锁外检查，提高性能）
        stack_names = [t.__name__ for t in self._resolution_stack]
        if interface.__name__ in stack_names:
            cycle = " -> ".join(stack_names + [interface.__name__])
            raise RuntimeError(f"检测到循环依赖: {cycle}")

        with self._lock:
            # 再次检查（锁内）
            stack_names = [t.__name__ for t in self._resolution_stack]
            if interface.__name__ in stack_names:
                cycle = " -> ".join(stack_names + [interface.__name__])
                raise RuntimeError(f"检测到循环依赖: {cycle}")

            if interface not in self._services:
                raise KeyError(f"服务未注册: {interface.__name__}")

            # 添加到解析栈
            self._resolution_stack.append(interface)

            try:
                descriptor = self._services[interface]

                # 根据生命周期返回实例
                if descriptor.lifetime == ServiceLifetime.SINGLETON:
                    return self._get_singleton(descriptor)
                elif descriptor.lifetime == ServiceLifetime.SCOPED:
                    if scope_id is None:
                        raise ValueError(f"作用域服务 {interface.__name__} 需要提供 scope_id")
                    return self._get_scoped(descriptor, scope_id)
                else:  # TRANSIENT
                    return self._create_instance(descriptor)
            except Exception:
                # 发生异常时从栈中移除
                if self._resolution_stack and self._resolution_stack[-1] == interface:
                    self._resolution_stack.pop()
                raise
            finally:
                # 正常完成后从栈中移除
                if self._resolution_stack and self._resolution_stack[-1] == interface:
                    self._resolution_stack.pop()
    
    def _get_singleton(self, descriptor: ServiceDescriptor) -> Any:
        """获取单例实例"""
        interface = descriptor.interface
        
        if interface not in self._singletons:
            instance = self._create_instance(descriptor)
            self._singletons[interface] = instance
            descriptor.instance = instance
            logger.debug(f"创建单例: {interface.__name__}")
        
        return self._singletons[interface]
    
    def _get_scoped(self, descriptor: ServiceDescriptor, scope_id: str) -> Any:
        """获取作用域实例"""
        interface = descriptor.interface
        
        if scope_id not in self._scopes:
            self._scopes[scope_id] = {}
        
        scope = self._scopes[scope_id]
        
        if interface not in scope:
            instance = self._create_instance(descriptor)
            scope[interface] = instance
            logger.debug(f"创建作用域实例: {interface.__name__} (scope: {scope_id})")
        
        return scope[interface]
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建实例"""
        implementation = descriptor.implementation
        
        # 如果是工厂函数，直接调用
        if descriptor.factory:
            return self._invoke_with_injection(descriptor.factory)
        
        # 如果是类，自动注入构造函数参数
        if isinstance(implementation, type):
            return self._create_class_instance(implementation)
        
        # 其他情况直接调用
        return implementation()
    
    def _create_class_instance(self, cls: Type) -> Any:
        """创建类实例，自动注入依赖"""
        # 获取构造函数签名
        try:
            sig = inspect.signature(cls.__init__)
            params = list(sig.parameters.items())[1:]  # 排除 self
        except (ValueError, TypeError):
            # 没有自定义构造函数
            return cls()
        
        # 解析参数
        kwargs = {}
        
        # 获取类的全局命名空间用于解析前向引用
        globalns = getattr(sys.modules.get(cls.__module__, {}), '__dict__', {})
        
        for param_name, param in params:
            if param.default is not inspect.Parameter.empty:
                # 有默认值，跳过
                continue
            
            # 尝试从类型注解解析
            if param.annotation is not inspect.Parameter.empty:
                annotation = param.annotation
                
                # 处理字符串注解（前向引用）
                if isinstance(annotation, str):
                    # 尝试使用get_type_hints解析
                    try:
                        hints = get_type_hints(cls, globalns=globalns)
                        if param_name in hints:
                            annotation = hints[param_name]
                        else:
                            # 尝试直接从全局命名空间解析
                            if annotation in globalns:
                                annotation = globalns[annotation]
                            else:
                                continue
                    except Exception:
                        # 回退到全局命名空间解析
                        if annotation in globalns:
                            annotation = globalns[annotation]
                        else:
                            continue
                
                # 跳过非类型注解
                if not isinstance(annotation, type):
                    continue
                
                # 检查是否已注册
                if not self.is_registered(annotation):
                    continue
                
                # 检查循环依赖 - 在调用resolve之前
                stack_names = [t.__name__ for t in self._resolution_stack]
                if annotation.__name__ in stack_names:
                    cycle = " -> ".join(stack_names + [annotation.__name__])
                    raise RuntimeError(f"检测到循环依赖: {cycle}")
                
                try:
                    dependency = self.resolve(annotation)
                    kwargs[param_name] = dependency
                except (KeyError, ValueError):
                    # 无法解析的依赖，跳过
                    pass
                # RuntimeError 不捕获，让它传播上去
        
        # 创建实例
        try:
            return cls(**kwargs)
        except TypeError as e:
            # 如果自动注入失败，尝试无参构造
            logger.warning(f"自动注入失败 {cls.__name__}: {e}，尝试无参构造")
            return cls()
    
    def _invoke_with_injection(self, func: Callable) -> Any:
        """调用函数，自动注入参数"""
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.items())
        except (ValueError, TypeError):
            return func()
        
        kwargs = {}
        for param_name, param in params:
            if param.default is not inspect.Parameter.empty:
                continue
            
            if param.annotation is not inspect.Parameter.empty:
                try:
                    dependency = self.resolve(param.annotation)
                    kwargs[param_name] = dependency
                except (KeyError, ValueError):
                    pass
        
        try:
            return func(**kwargs)
        except TypeError:
            return func()
    
    def create_scope(self, scope_id: str) -> 'Scope':
        """
        创建作用域
        
        Args:
            scope_id: 作用域ID
            
        Returns:
            Scope: 作用域对象
        """
        return Scope(self, scope_id)
    
    def clear_scope(self, scope_id: str) -> None:
        """
        清理作用域
        
        Args:
            scope_id: 作用域ID
        """
        with self._lock:
            if scope_id in self._scopes:
                del self._scopes[scope_id]
                logger.debug(f"清理作用域: {scope_id}")
    
    def clear_singletons(self) -> None:
        """清理所有单例"""
        with self._lock:
            self._singletons.clear()
            logger.debug("清理所有单例")
    
    def is_registered(self, interface: Type) -> bool:
        """
        检查服务是否已注册
        
        Args:
            interface: 服务接口类型
            
        Returns:
            bool: 是否已注册
        """
        return interface in self._services
    
    def get_registered_services(self) -> List[str]:
        """
        获取所有已注册的服务名称
        
        Returns:
            List[str]: 服务名称列表
        """
        return [desc.interface.__name__ for desc in self._services.values()]


class Scope:
    """
    作用域上下文管理器
    
    用于管理作用域生命周期内的服务实例。
    
    使用示例:
        with container.create_scope("request_1") as scope:
            service = scope.resolve(IService)
            # 使用服务...
        # 作用域结束时自动清理
    """
    
    def __init__(self, container: DIContainer, scope_id: str):
        """
        初始化作用域
        
        Args:
            container: DI 容器
            scope_id: 作用域ID
        """
        self._container = container
        self._scope_id = scope_id
        self._disposed = False
    
    def __enter__(self) -> 'Scope':
        """进入作用域"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出作用域，自动清理"""
        self.dispose()
    
    def resolve(self, interface: Type[T]) -> T:
        """
        在作用域内解析服务
        
        Args:
            interface: 服务接口类型
            
        Returns:
            T: 服务实例
        """
        if self._disposed:
            raise RuntimeError("作用域已销毁")
        
        return self._container.resolve(interface, self._scope_id)
    
    def dispose(self) -> None:
        """销毁作用域，清理资源"""
        if not self._disposed:
            self._container.clear_scope(self._scope_id)
            self._disposed = True
            logger.debug(f"作用域已销毁: {self._scope_id}")


# 全局容器实例
_default_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """
    获取全局 DI 容器实例
    
    Returns:
        DIContainer: DI 容器单例
    """
    global _default_container
    
    if _default_container is None:
        with _container_lock:
            if _default_container is None:
                _default_container = DIContainer()
                logger.debug("创建全局 DI 容器")
    
    return _default_container


def configure_services(config_action: Callable[[DIContainer], None]) -> DIContainer:
    """
    配置全局容器服务
    
    Args:
        config_action: 配置动作，接收容器参数
        
    Returns:
        DIContainer: 配置后的容器
        
    Example:
        def configure(container):
            container.register_singleton(IConfig, UIConfig)
            container.register_singleton(IScalingManager, ScalingManager)
        
        container = configure_services(configure)
    """
    container = get_container()
    config_action(container)
    return container


# 便捷函数
def register_singleton(interface: Type[T], implementation: Union[Type, Callable]) -> DIContainer:
    """便捷函数：注册单例服务"""
    return get_container().register_singleton(interface, implementation)


def register_transient(interface: Type[T], implementation: Union[Type, Callable]) -> DIContainer:
    """便捷函数：注册瞬态服务"""
    return get_container().register_transient(interface, implementation)


def resolve(interface: Type[T]) -> T:
    """便捷函数：解析服务"""
    return get_container().resolve(interface)
