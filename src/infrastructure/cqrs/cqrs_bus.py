#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CQRS (Command Query Responsibility Segregation) 基础设施模块

提供命令和查询的分离处理机制。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# 类型变量
TCommand = TypeVar('TCommand')
TResult = TypeVar('TResult')


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[list] = None
    
    @staticmethod
    def ok(message: str = "操作成功", data: Any = None) -> 'CommandResult':
        """创建成功的结果"""
        return CommandResult(success=True, message=message, data=data)
    
    @staticmethod
    def fail(message: str = "操作失败", errors: list = None) -> 'CommandResult':
        """创建失败的结果"""
        return CommandResult(success=False, message=message, errors=errors or [])


@dataclass
class QueryResult(Generic[TResult]):
    """查询执行结果"""
    success: bool
    data: Optional[TResult]
    message: str = ""
    total_count: int = 0
    
    @staticmethod
    def ok(data: TResult, total_count: int = 0) -> 'QueryResult[TResult]':
        """创建成功的结果"""
        return QueryResult(success=True, data=data, total_count=total_count)
    
    @staticmethod
    def fail(message: str = "查询失败") -> 'QueryResult[TResult]':
        """创建失败的结果"""
        return QueryResult(success=False, data=None, message=message)


class Command(ABC, Generic[TCommand]):
    """
    命令基类
    
    封装一个写操作（创建、更新、删除）。
    """
    
    def __init__(self, data: TCommand):
        """
        初始化命令
        
        Args:
            data: 命令数据
        """
        self.data = data
        self.timestamp = __import__('time').time()
    
    def validate(self) -> bool:
        """
        验证命令数据
        
        Returns:
            bool: 验证是否通过
        """
        return True


class Query(ABC, Generic[TResult]):
    """
    查询基类
    
    封装一个读操作。
    """
    
    def __init__(self):
        """初始化查询"""
        self.timestamp = __import__('time').time()
    
    def validate(self) -> bool:
        """
        验证查询参数
        
        Returns:
            bool: 验证是否通过
        """
        return True


class CommandHandler(ABC, Generic[TCommand]):
    """
    命令处理器基类
    
    处理命令的执行逻辑。
    """
    
    @abstractmethod
    def handle(self, command: Command[TCommand]) -> CommandResult:
        """
        处理命令
        
        Args:
            command: 命令对象
            
        Returns:
            CommandResult: 执行结果
        """
        pass
    
    def can_handle(self, command: Command) -> bool:
        """
        检查是否能处理此命令
        
        Args:
            command: 命令对象
            
        Returns:
            bool: 是否能处理
        """
        return True


class QueryHandler(ABC, Generic[TResult]):
    """
    查询处理器基类
    
    处理查询的执行逻辑。
    """
    
    @abstractmethod
    def handle(self, query: Query[TResult]) -> QueryResult[TResult]:
        """
        处理查询
        
        Args:
            query: 查询对象
            
        Returns:
            QueryResult[TResult]: 查询结果
        """
        pass
    
    def can_handle(self, query: Query) -> bool:
        """
        检查是否能处理此查询
        
        Args:
            query: 查询对象
            
        Returns:
            bool: 是否能处理
        """
        return True


class CQRSBus:
    """
    CQRS总线
    
    负责分发命令和查询到对应的处理器。
    """
    
    def __init__(self):
        """初始化总线"""
        self._command_handlers: Dict[type, CommandHandler] = {}
        self._query_handlers: Dict[type, QueryHandler] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_command_handler(
        self,
        command_type: type,
        handler: CommandHandler
    ) -> None:
        """
        注册命令处理器
        
        Args:
            command_type: 命令类型
            handler: 处理器实例
        """
        self._command_handlers[command_type] = handler
        self.logger.debug(f"注册命令处理器: {command_type.__name__}")
    
    def register_query_handler(
        self,
        query_type: type,
        handler: QueryHandler
    ) -> None:
        """
        注册查询处理器
        
        Args:
            query_type: 查询类型
            handler: 处理器实例
        """
        self._query_handlers[query_type] = handler
        self.logger.debug(f"注册查询处理器: {query_type.__name__}")
    
    def execute_command(self, command: Command) -> CommandResult:
        """
        执行命令
        
        Args:
            command: 命令对象
            
        Returns:
            CommandResult: 执行结果
        """
        # 验证命令
        if not command.validate():
            return CommandResult.fail("命令验证失败")
        
        # 查找处理器
        handler = self._command_handlers.get(type(command))
        if not handler:
            return CommandResult.fail(f"未找到命令处理器: {type(command).__name__}")
        
        try:
            self.logger.info(f"执行命令: {type(command).__name__}")
            result = handler.handle(command)
            return result
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            return CommandResult.fail(f"执行异常: {str(e)}")
    
    def execute_query(self, query: Query[TResult]) -> QueryResult[TResult]:
        """
        执行查询
        
        Args:
            query: 查询对象
            
        Returns:
            QueryResult[TResult]: 查询结果
        """
        # 验证查询
        if not query.validate():
            return QueryResult.fail("查询验证失败")
        
        # 查找处理器
        handler = self._query_handlers.get(type(query))
        if not handler:
            return QueryResult.fail(f"未找到查询处理器: {type(query).__name__}")
        
        try:
            self.logger.debug(f"执行查询: {type(query).__name__}")
            result = handler.handle(query)
            return result
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            return QueryResult.fail(f"执行异常: {str(e)}")


# 全局CQRS总线实例
_cqrs_bus: Optional[CQRSBus] = None


def get_cqrs_bus() -> CQRSBus:
    """
    获取CQRS总线实例
    
    Returns:
        CQRSBus: CQRS总线
    """
    global _cqrs_bus
    if _cqrs_bus is None:
        _cqrs_bus = CQRSBus()
    return _cqrs_bus
