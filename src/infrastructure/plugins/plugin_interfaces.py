#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
插件系统接口定义

定义插件系统的核心接口，包括：
- IPlugin: 插件接口
- IPluginManager: 插件管理器接口
- IHook: 钩子接口
- IExtensionPoint: 扩展点接口
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from src.infrastructure.interfaces import IService


class IPlugin(ABC):
    """
    插件接口
    
    所有插件都必须实现此接口。
    
    生命周期:
    1. __init__: 初始化（不执行耗时操作）
    2. initialize: 初始化插件（可执行耗时操作）
    3. execute: 执行插件功能
    4. shutdown: 关闭插件
    
    示例:
        >>> class MyPlugin(IPlugin):
        ...     def get_name(self) -> str:
        ...         return "MyPlugin"
        ...     
        ...     def get_version(self) -> str:
        ...         return "1.0.0"
        ...     
        ...     def initialize(self) -> bool:
        ...         return True
        ...     
        ...     def execute(self, *args, **kwargs) -> Any:
        ...         return "result"
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取插件名称
        
        Returns:
            str: 插件唯一标识名称
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """
        获取插件版本
        
        Returns:
            str: 版本号（如 "1.0.0"）
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取插件描述
        
        Returns:
            str: 插件描述信息
        """
        pass
    
    @abstractmethod
    def get_author(self) -> str:
        """
        获取插件作者
        
        Returns:
            str: 作者信息
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """
        获取插件依赖
        
        Returns:
            List[str]: 依赖的插件名称列表
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化插件
        
        在此方法中执行插件初始化逻辑，如：
        - 加载配置
        - 建立连接
        - 注册钩子
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        执行插件功能
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 执行结果
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        关闭插件
        
        在此方法中执行清理工作，如：
        - 释放资源
        - 关闭连接
        - 注销钩子
        """
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查插件是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        pass


class IPluginManager(IService):
    """
    插件管理器接口
    
    负责插件的生命周期管理。
    """
    
    @abstractmethod
    def register_plugin(self, plugin_class: Type[IPlugin]) -> bool:
        """
        注册插件
        
        Args:
            plugin_class: 插件类
            
        Returns:
            bool: 注册是否成功
        """
        pass
    
    @abstractmethod
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    @abstractmethod
    def load_plugin(self, plugin_name: str) -> bool:
        """
        加载并初始化插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 加载是否成功
        """
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """
        获取已加载的插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[IPlugin]: 插件实例
        """
        pass
    
    @abstractmethod
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        列出所有已注册的插件
        
        Returns:
            List[Dict[str, Any]]: 插件信息列表
        """
        pass
    
    @abstractmethod
    def list_loaded_plugins(self) -> List[str]:
        """
        列出所有已加载的插件
        
        Returns:
            List[str]: 插件名称列表
        """
        pass
    
    @abstractmethod
    def execute_plugin(self, plugin_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        执行指定插件
        
        Args:
            plugin_name: 插件名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 执行结果
        """
        pass
    
    @abstractmethod
    def check_dependencies(self, plugin_name: str) -> bool:
        """
        检查插件依赖是否满足
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 依赖是否满足
        """
        pass


class IHook(ABC):
    """
    钩子接口
    
    定义钩子点，允许插件在特定时机插入自定义逻辑。
    
    示例:
        >>> class PreQueryHook(IHook):
        ...     def get_name(self) -> str:
        ...         return "pre.query"
        ...     
        ...     def execute(self, query: str) -> str:
        ...         # 修改查询语句
        ...         return query + " LIMIT 100"
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取钩子名称
        
        Returns:
            str: 钩子唯一标识
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取钩子描述
        
        Returns:
            str: 钩子描述
        """
        pass
    
    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        执行钩子逻辑
        
        Args:
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 执行结果
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        获取钩子优先级
        
        Returns:
            int: 优先级（值越小优先级越高）
        """
        pass


class IHookManager(ABC):
    """
    钩子管理器接口
    
    管理所有钩子的注册和执行。
    """
    
    @abstractmethod
    def register_hook(self, hook_point: str, hook: IHook) -> str:
        """
        注册钩子
        
        Args:
            hook_point: 钩子点名称
            hook: 钩子实例
            
        Returns:
            str: 钩子ID
        """
        pass
    
    @abstractmethod
    def unregister_hook(self, hook_id: str) -> bool:
        """
        注销钩子
        
        Args:
            hook_id: 钩子ID
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    @abstractmethod
    def execute_hooks(self, hook_point: str, *args: Any, **kwargs: Any) -> List[Any]:
        """
        执行指定钩子点的所有钩子
        
        Args:
            hook_point: 钩子点名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            List[Any]: 所有钩子的执行结果
        """
        pass
    
    @abstractmethod
    def execute_hooks_chain(
        self, 
        hook_point: str, 
        initial_value: Any,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        链式执行钩子（前一个钩子的结果作为后一个钩子的输入）
        
        Args:
            hook_point: 钩子点名称
            initial_value: 初始值
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 最终执行结果
        """
        pass
    
    @abstractmethod
    def list_hooks(self, hook_point: Optional[str] = None) -> Dict[str, List[str]]:
        """
        列出已注册的钩子
        
        Args:
            hook_point: 钩子点名称（可选）
            
        Returns:
            Dict[str, List[str]]: 钩子列表
        """
        pass


class IExtensionPoint(ABC):
    """
    扩展点接口
    
    定义扩展点，允许插件扩展特定功能。
    
    示例:
        >>> class IDataExporter(IExtensionPoint):
        ...     def get_name(self) -> str:
        ...         return "data.exporter"
        ...     
        ...     def export(self, data: Any, format: str) -> str:
        ...         pass
    """
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取扩展点名称
        
        Returns:
            str: 扩展点唯一标识
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取扩展点描述
        
        Returns:
            str: 扩展点描述
        """
        pass


class IExtensionRegistry(ABC):
    """
    扩展注册中心接口
    
    管理所有扩展点的注册和获取。
    """
    
    @abstractmethod
    def register_extension_point(
        self, 
        extension_point: Type[IExtensionPoint]
    ) -> bool:
        """
        注册扩展点
        
        Args:
            extension_point: 扩展点类
            
        Returns:
            bool: 注册是否成功
        """
        pass
    
    @abstractmethod
    def register_extension(
        self, 
        extension_point_name: str,
        extension: Type[IExtensionPoint],
        plugin_name: Optional[str] = None
    ) -> str:
        """
        注册扩展
        
        Args:
            extension_point_name: 扩展点名称
            extension: 扩展实现类
            plugin_name: 所属插件名称（可选）
            
        Returns:
            str: 扩展ID
        """
        pass
    
    @abstractmethod
    def unregister_extension(self, extension_id: str) -> bool:
        """
        注销扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 注销是否成功
        """
        pass
    
    @abstractmethod
    def get_extensions(
        self, 
        extension_point_name: str
    ) -> List[IExtensionPoint]:
        """
        获取指定扩展点的所有扩展
        
        Args:
            extension_point_name: 扩展点名称
            
        Returns:
            List[IExtensionPoint]: 扩展实例列表
        """
        pass
    
    @abstractmethod
    def list_extension_points(self) -> List[str]:
        """
        列出所有扩展点
        
        Returns:
            List[str]: 扩展点名称列表
        """
        pass
