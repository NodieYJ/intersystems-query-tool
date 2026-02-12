#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
策略模式框架

提供策略模式的基础设施，支持：
- 策略定义和注册
- 运行时策略切换
- 策略组合
- 上下文管理
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

from src.infrastructure.exceptions import BusinessException, NotFoundException

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


class IStrategy(ABC, Generic[T, R]):
    """
    策略接口
    
    所有策略都必须实现此接口。
    
    类型参数:
        T: 输入类型
        R: 返回类型
    
    示例:
        >>> class DiscountStrategy(IStrategy[Order, float]):
        ...     def execute(self, order: Order) -> float:
        ...         return order.total * 0.9
        ...     
        ...     def get_name(self) -> str:
        ...         return "10% Discount"
    """
    
    @abstractmethod
    def execute(self, context: T) -> R:
        """
        执行策略
        
        Args:
            context: 策略上下文
            
        Returns:
            R: 执行结果
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取策略名称
        
        Returns:
            str: 策略唯一标识名称
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            str: 策略描述
        """
        pass
    
    def validate(self, context: T) -> bool:
        """
        验证上下文是否适用于此策略
        
        Args:
            context: 策略上下文
            
        Returns:
            bool: 是否适用
        """
        return True


class StrategyContext(Generic[T, R]):
    """
    策略上下文类
    
    维护当前策略并提供执行入口。
    
    示例:
        >>> context = StrategyContext[Order, float]()
        >>> context.set_strategy(DiscountStrategy())
        >>> result = context.execute(order)
    """
    
    def __init__(self, default_strategy: Optional[IStrategy[T, R]] = None):
        """
        初始化策略上下文
        
        Args:
            default_strategy: 默认策略
        """
        self._current_strategy: Optional[IStrategy[T, R]] = default_strategy
        self._strategy_history: List[IStrategy[T, R]] = []
        self._execution_count = 0
    
    def set_strategy(self, strategy: IStrategy[T, R]) -> None:
        """
        设置当前策略
        
        Args:
            strategy: 策略实例
        """
        if self._current_strategy:
            self._strategy_history.append(self._current_strategy)
        
        self._current_strategy = strategy
        logger.debug(f"Strategy set to: {strategy.get_name()}")
    
    def get_strategy(self) -> Optional[IStrategy[T, R]]:
        """
        获取当前策略
        
        Returns:
            Optional[IStrategy[T, R]]: 当前策略
        """
        return self._current_strategy
    
    def execute(self, context: T) -> R:
        """
        执行当前策略
        
        Args:
            context: 策略上下文
            
        Returns:
            R: 执行结果
            
        Raises:
            BusinessException: 没有设置策略
        """
        if not self._current_strategy:
            raise BusinessException(
                "No strategy set",
                "STR_001",
                {"context": type(context).__name__}
            )
        
        # 验证策略
        if not self._current_strategy.validate(context):
            raise BusinessException(
                f"Strategy '{self._current_strategy.get_name()}' is not applicable",
                "STR_002"
            )
        
        self._execution_count += 1
        return self._current_strategy.execute(context)
    
    def restore_previous(self) -> bool:
        """
        恢复上一个策略
        
        Returns:
            bool: 是否成功恢复
        """
        if not self._strategy_history:
            return False
        
        self._current_strategy = self._strategy_history.pop()
        logger.debug(f"Strategy restored to: {self._current_strategy.get_name()}")
        return True
    
    def get_execution_count(self) -> int:
        """
        获取执行次数
        
        Returns:
            int: 执行次数
        """
        return self._execution_count


class StrategyRegistry:
    """
    策略注册中心
    
    管理所有策略的注册和获取。
    
    单例模式确保全局唯一。
    
    示例:
        >>> registry = StrategyRegistry.get_instance()
        >>> 
        >>> # 注册策略
        >>> registry.register("discount", DiscountStrategy)
        >>> registry.register("premium", PremiumDiscountStrategy)
        >>> 
        >>> # 获取策略
        >>> strategy = registry.get("discount")
        >>> 
        >>> # 创建上下文并执行
        >>> context = StrategyContext()
        >>> context.set_strategy(strategy())
        >>> result = context.execute(order)
    """
    
    _instance: Optional['StrategyRegistry'] = None
    
    def __new__(cls) -> 'StrategyRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._strategies: Dict[str, Type[IStrategy]] = {}
        self._initialized = True
        
        logger.info("StrategyRegistry initialized")
    
    @classmethod
    def get_instance(cls) -> 'StrategyRegistry':
        """获取单例实例"""
        return cls()
    
    def register(
        self,
        name: str,
        strategy_class: Type[IStrategy],
        overwrite: bool = False
    ) -> bool:
        """
        注册策略
        
        Args:
            name: 策略名称
            strategy_class: 策略类
            overwrite: 是否允许覆盖已有策略
            
        Returns:
            bool: 注册是否成功
        """
        if name in self._strategies and not overwrite:
            logger.warning(f"Strategy '{name}' is already registered")
            return False
        
        self._strategies[name] = strategy_class
        logger.info(f"Strategy registered: {name}")
        return True
    
    def unregister(self, name: str) -> bool:
        """
        注销策略
        
        Args:
            name: 策略名称
            
        Returns:
            bool: 注销是否成功
        """
        if name not in self._strategies:
            return False
        
        del self._strategies[name]
        logger.info(f"Strategy unregistered: {name}")
        return True
    
    def get(self, name: str) -> Optional[Type[IStrategy]]:
        """
        获取策略类
        
        Args:
            name: 策略名称
            
        Returns:
            Optional[Type[IStrategy]]: 策略类
        """
        return self._strategies.get(name)
    
    def create(self, name: str, *args: Any, **kwargs: Any) -> Optional[IStrategy]:
        """
        创建策略实例
        
        Args:
            name: 策略名称
            *args: 构造参数
            **kwargs: 关键字参数
            
        Returns:
            Optional[IStrategy]: 策略实例
            
        Raises:
            NotFoundException: 策略不存在
        """
        strategy_class = self.get(name)
        
        if not strategy_class:
            raise NotFoundException("Strategy", name)
        
        return strategy_class(*args, **kwargs)
    
    def list_strategies(self) -> List[str]:
        """
        列出所有已注册的策略
        
        Returns:
            List[str]: 策略名称列表
        """
        return list(self._strategies.keys())
    
    def get_strategy_info(self, name: str) -> Optional[Dict[str, str]]:
        """
        获取策略信息
        
        Args:
            name: 策略名称
            
        Returns:
            Optional[Dict[str, str]]: 策略信息
        """
        strategy_class = self.get(name)
        
        if not strategy_class:
            return None
        
        # 创建临时实例获取信息
        try:
            temp_instance = strategy_class()
            return {
                "name": temp_instance.get_name(),
                "description": temp_instance.get_description(),
                "class": strategy_class.__name__,
                "module": strategy_class.__module__
            }
        except:
            return {
                "name": name,
                "class": strategy_class.__name__,
                "module": strategy_class.__module__
            }
    
    def clear(self) -> None:
        """清空所有策略"""
        self._strategies.clear()
        logger.info("Strategy registry cleared")


class CompositeStrategy(IStrategy[T, R]):
    """
    组合策略
    
    将多个策略组合在一起，按顺序执行。
    
    示例:
        >>> composite = CompositeStrategy[Order, float]()
        >>> composite.add_strategy(DiscountStrategy())
        >>> composite.add_strategy(TaxStrategy())
        >>> 
        >>> # 执行所有策略
        >>> result = composite.execute(order)
    """
    
    def __init__(self, name: str = "Composite", description: str = ""):
        """
        初始化组合策略
        
        Args:
            name: 策略名称
            description: 策略描述
        """
        self._name = name
        self._description = description
        self._strategies: List[IStrategy[T, R]] = []
        self._combiner: Optional[Callable[[List[R]], R]] = None
    
    def add_strategy(self, strategy: IStrategy[T, R]) -> None:
        """
        添加策略
        
        Args:
            strategy: 策略实例
        """
        self._strategies.append(strategy)
        logger.debug(f"Strategy added to composite: {strategy.get_name()}")
    
    def remove_strategy(self, strategy: IStrategy[T, R]) -> bool:
        """
        移除策略
        
        Args:
            strategy: 策略实例
            
        Returns:
            bool: 是否成功移除
        """
        if strategy in self._strategies:
            self._strategies.remove(strategy)
            return True
        return False
    
    def set_combiner(self, combiner: Callable[[List[R]], R]) -> None:
        """
        设置结果合并器
        
        Args:
            combiner: 合并函数，接收所有策略的结果列表，返回最终结果
        """
        self._combiner = combiner
    
    def execute(self, context: T) -> R:
        """
        执行所有策略
        
        Args:
            context: 策略上下文
            
        Returns:
            R: 执行结果
        """
        results = []
        
        for strategy in self._strategies:
            try:
                if strategy.validate(context):
                    result = strategy.execute(context)
                    results.append(result)
            except Exception as e:
                logger.error(f"Strategy execution failed: {strategy.get_name()}, error: {e}")
        
        # 合并结果
        if self._combiner:
            return self._combiner(results)
        
        # 默认返回最后一个结果
        if results:
            return results[-1]
        
        raise BusinessException("No strategy produced a result", "STR_003")
    
    def get_name(self) -> str:
        return self._name
    
    def get_description(self) -> str:
        return self._description
    
    def validate(self, context: T) -> bool:
        """至少有一个策略适用即可"""
        return any(s.validate(context) for s in self._strategies)


# 便捷函数
def get_strategy_registry() -> StrategyRegistry:
    """获取全局策略注册中心"""
    return StrategyRegistry.get_instance()


def register_strategy(
    name: str,
    strategy_class: Type[IStrategy],
    overwrite: bool = False
) -> bool:
    """
    便捷函数：注册策略
    
    Args:
        name: 策略名称
        strategy_class: 策略类
        overwrite: 是否允许覆盖
        
    Returns:
        bool: 注册是否成功
    """
    return get_strategy_registry().register(name, strategy_class, overwrite)


def get_strategy(name: str) -> Optional[Type[IStrategy]]:
    """
    便捷函数：获取策略
    
    Args:
        name: 策略名称
        
    Returns:
        Optional[Type[IStrategy]]: 策略类
    """
    return get_strategy_registry().get(name)
