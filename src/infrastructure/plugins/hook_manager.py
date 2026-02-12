#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
钩子管理器实现

管理钩子的注册和执行，支持：
- 钩子注册和注销
- 批量执行钩子
- 链式执行钩子
- 优先级控制
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from src.infrastructure.plugins.plugin_interfaces import IHook, IHookManager

logger = logging.getLogger(__name__)


class Hook(IHook):
    """
    钩子基类实现
    
    简化钩子创建。
    
    示例:
        >>> hook = Hook("pre.query", lambda query: query + " LIMIT 100")
    """
    
    def __init__(
        self,
        name: str,
        callback: Callable[..., Any],
        description: str = "",
        priority: int = 100
    ):
        """
        初始化钩子
        
        Args:
            name: 钩子名称
            callback: 回调函数
            description: 描述
            priority: 优先级
        """
        self._name = name
        self._callback = callback
        self._description = description
        self._priority = priority
    
    def get_name(self) -> str:
        return self._name
    
    def get_description(self) -> str:
        return self._description
    
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        return self._callback(*args, **kwargs)
    
    def get_priority(self) -> int:
        return self._priority


class HookManager(IHookManager):
    """
    钩子管理器实现
    
    管理所有钩子的注册和执行。
    
    单例模式确保全局唯一。
    
    示例:
        >>> manager = HookManager.get_instance()
        >>> 
        >>> # 注册钩子
        >>> manager.register_hook("pre.query", my_hook)
        >>> 
        >>> # 执行钩子
        >>> results = manager.execute_hooks("pre.query", query)
        >>> 
        >>> # 链式执行
        >>> result = manager.execute_hooks_chain("filter.data", data)
    """
    
    _instance: Optional['HookManager'] = None
    
    def __new__(cls) -> 'HookManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._hooks: Dict[str, List[Dict[str, Any]]] = {}
        self._hook_counter = 0
        self._initialized = True
        
        logger.info("HookManager initialized")
    
    @classmethod
    def get_instance(cls) -> 'HookManager':
        """获取单例实例"""
        return cls()
    
    def register_hook(self, hook_point: str, hook: IHook) -> str:
        """
        注册钩子
        
        Args:
            hook_point: 钩子点名称
            hook: 钩子实例
            
        Returns:
            str: 钩子ID
        """
        self._hook_counter += 1
        hook_id = f"{hook_point}_{self._hook_counter}"
        
        if hook_point not in self._hooks:
            self._hooks[hook_point] = []
        
        self._hooks[hook_point].append({
            "id": hook_id,
            "hook": hook,
            "priority": hook.get_priority()
        })
        
        # 按优先级排序
        self._hooks[hook_point].sort(key=lambda x: x["priority"])
        
        logger.debug(f"Hook registered: {hook_id} at {hook_point}")
        return hook_id
    
    def unregister_hook(self, hook_id: str) -> bool:
        """
        注销钩子
        
        Args:
            hook_id: 钩子ID
            
        Returns:
            bool: 注销是否成功
        """
        for hook_point, hooks in self._hooks.items():
            for i, hook_info in enumerate(hooks):
                if hook_info["id"] == hook_id:
                    hooks.pop(i)
                    logger.debug(f"Hook unregistered: {hook_id}")
                    return True
        
        return False
    
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
        results = []
        
        if hook_point not in self._hooks:
            return results
        
        for hook_info in self._hooks[hook_point]:
            try:
                result = hook_info["hook"].execute(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook execution failed: {hook_info['id']}, error: {e}")
                results.append(e)
        
        return results
    
    def execute_hooks_chain(
        self,
        hook_point: str,
        initial_value: Any,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        链式执行钩子
        
        前一个钩子的结果作为后一个钩子的第一个参数。
        
        Args:
            hook_point: 钩子点名称
            initial_value: 初始值
            *args: 其他位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 最终执行结果
        """
        if hook_point not in self._hooks:
            return initial_value
        
        value = initial_value
        
        for hook_info in self._hooks[hook_point]:
            try:
                # 将前一个结果作为第一个参数
                value = hook_info["hook"].execute(value, *args, **kwargs)
            except Exception as e:
                logger.error(f"Hook chain execution failed: {hook_info['id']}, error: {e}")
        
        return value
    
    def list_hooks(self, hook_point: Optional[str] = None) -> Dict[str, List[str]]:
        """
        列出已注册的钩子
        
        Args:
            hook_point: 钩子点名称（可选）
            
        Returns:
            Dict[str, List[str]]: 钩子列表
        """
        if hook_point:
            if hook_point in self._hooks:
                return {
                    hook_point: [h["id"] for h in self._hooks[hook_point]]
                }
            return {}
        
        return {
            point: [h["id"] for h in hooks]
            for point, hooks in self._hooks.items()
        }
    
    def clear_hooks(self, hook_point: Optional[str] = None) -> None:
        """
        清除钩子
        
        Args:
            hook_point: 钩子点名称（可选，None则清除所有）
        """
        if hook_point:
            if hook_point in self._hooks:
                del self._hooks[hook_point]
                logger.debug(f"Hooks cleared: {hook_point}")
        else:
            self._hooks.clear()
            logger.debug("All hooks cleared")
    
    def get_hook_count(self, hook_point: Optional[str] = None) -> int:
        """
        获取钩子数量
        
        Args:
            hook_point: 钩子点名称（可选）
            
        Returns:
            int: 钩子数量
        """
        if hook_point:
            return len(self._hooks.get(hook_point, []))
        
        return sum(len(hooks) for hooks in self._hooks.values())


# 便捷函数
def get_hook_manager() -> HookManager:
    """获取全局钩子管理器"""
    return HookManager.get_instance()


def add_hook(
    hook_point: str,
    callback: Callable[..., Any],
    priority: int = 100,
    description: str = ""
) -> str:
    """
    便捷函数：添加钩子
    
    Args:
        hook_point: 钩子点名称
        callback: 回调函数
        priority: 优先级
        description: 描述
        
    Returns:
        str: 钩子ID
    """
    hook = Hook(hook_point, callback, description, priority)
    return get_hook_manager().register_hook(hook_point, hook)


def apply_hooks(hook_point: str, value: Any, *args: Any, **kwargs: Any) -> Any:
    """
    便捷函数：应用钩子链
    
    Args:
        hook_point: 钩子点名称
        value: 初始值
        *args: 其他参数
        **kwargs: 关键字参数
        
    Returns:
        Any: 处理后的值
    """
    return get_hook_manager().execute_hooks_chain(hook_point, value, *args, **kwargs)
