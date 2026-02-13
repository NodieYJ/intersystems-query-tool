#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据服务CQRS实现

提供具体的数据查询和命令处理。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from src.infrastructure.cqrs.cqrs_bus import (
    Command, CommandHandler, CommandResult,
    Query, QueryHandler, QueryResult
)


# ============================================================================
# 命令定义
# ============================================================================

@dataclass
class ExecuteQueryCommandData:
    """执行查询命令数据"""
    query: str
    params: Optional[List[Any]] = None


class ExecuteQueryCommand(Command[ExecuteQueryCommandData]):
    """执行SQL查询命令"""
    
    def __init__(self, query: str, params: Optional[List[Any]] = None):
        data = ExecuteQueryCommandData(query=query, params=params)
        super().__init__(data)


@dataclass
class UpdateDataCommandData:
    """更新数据命令数据"""
    query: str
    params: Optional[List[Any]] = None


class UpdateDataCommand(Command[UpdateDataCommandData]):
    """更新数据命令"""
    
    def __init__(self, query: str, params: Optional[List[Any]] = None):
        data = UpdateDataCommandData(query=query, params=params)
        super().__init__(data)


# ============================================================================
# 查询定义
# ============================================================================

@dataclass
class GetTableListQueryData:
    """获取表列表查询参数"""
    pass


class GetTableListQuery(Query[List[str]]):
    """获取所有表名查询"""
    
    def __init__(self):
        super().__init__()


@dataclass
class GetTableDataQueryData:
    """获取表数据查询参数"""
    table_name: str
    limit: int = 100
    offset: int = 0


class GetTableDataQuery(Query[List[Dict[str, Any]]]):
    """获取表数据查询"""
    
    def __init__(self, table_name: str, limit: int = 100, offset: int = 0):
        super().__init__()
        self.table_name = table_name
        self.limit = limit
        self.offset = offset
    
    def validate(self) -> bool:
        """验证查询参数"""
        return (
            bool(self.table_name) and
            self.limit > 0 and
            self.limit <= 10000 and
            self.offset >= 0
        )


# ============================================================================
# 命令处理器
# ============================================================================

class ExecuteQueryCommandHandler(CommandHandler[ExecuteQueryCommandData]):
    """执行查询命令处理器"""
    
    def __init__(self, data_service: Any):
        """
        初始化处理器
        
        Args:
            data_service: 数据服务实例
        """
        self.data_service = data_service
    
    def handle(self, command: ExecuteQueryCommand) -> CommandResult:
        """
        处理执行查询命令
        
        Args:
            command: 命令对象
            
        Returns:
            CommandResult: 执行结果
        """
        try:
            result = self.data_service.execute_query(
                command.data.query,
                command.data.params
            )
            return CommandResult.ok(
                message="查询执行成功",
                data=result
            )
        except Exception as e:
            return CommandResult.fail(
                message=f"查询执行失败: {str(e)}"
            )


class UpdateDataCommandHandler(CommandHandler[UpdateDataCommandData]):
    """更新数据命令处理器"""
    
    def __init__(self, data_service: Any):
        """
        初始化处理器
        
        Args:
            data_service: 数据服务实例
        """
        self.data_service = data_service
    
    def handle(self, command: UpdateDataCommand) -> CommandResult:
        """
        处理更新数据命令
        
        Args:
            command: 命令对象
            
        Returns:
            CommandResult: 执行结果
        """
        try:
            success = self.data_service.update_data(
                command.data.query,
                command.data.params
            )
            if success:
                return CommandResult.ok(
                    message="数据更新成功",
                    data={'affected_rows': 1}
                )
            else:
                return CommandResult.fail(
                    message="数据更新失败"
                )
        except Exception as e:
            return CommandResult.fail(
                message=f"数据更新异常: {str(e)}"
            )


# ============================================================================
# 查询处理器
# ============================================================================

class GetTableListQueryHandler(QueryHandler[List[str]]):
    """获取表列表查询处理器"""
    
    def __init__(self, data_service: Any):
        """
        初始化处理器
        
        Args:
            data_service: 数据服务实例
        """
        self.data_service = data_service
    
    def handle(self, query: GetTableListQuery) -> QueryResult[List[str]]:
        """
        处理获取表列表查询
        
        Args:
            query: 查询对象
            
        Returns:
            QueryResult[List[str]]: 表名列表
        """
        try:
            tables = self.data_service.get_table_names()
            return QueryResult.ok(
                data=tables,
                total_count=len(tables)
            )
        except Exception as e:
            return QueryResult.fail(
                message=f"获取表列表失败: {str(e)}"
            )


class GetTableDataQueryHandler(QueryHandler[List[Dict[str, Any]]]):
    """获取表数据查询处理器"""
    
    def __init__(self, data_service: Any):
        """
        初始化处理器
        
        Args:
            data_service: 数据服务实例
        """
        self.data_service = data_service
    
    def handle(self, query: GetTableDataQuery) -> QueryResult[List[Dict[str, Any]]]:
        """
        处理获取表数据查询
        
        Args:
            query: 查询对象
            
        Returns:
            QueryResult[List[Dict[str, Any]]]: 表数据
        """
        try:
            data = self.data_service.get_table_data(
                query.table_name,
                query.limit,
                query.offset
            )
            total_count = self.data_service.get_table_count(query.table_name)
            return QueryResult.ok(
                data=data,
                total_count=total_count
            )
        except Exception as e:
            return QueryResult.fail(
                message=f"获取表数据失败: {str(e)}"
            )


# ============================================================================
# 便捷函数
# ============================================================================

def register_data_service_cqrs(data_service: Any, cqrs_bus: Any) -> None:
    """
    注册数据服务CQRS处理器
    
    Args:
        data_service: 数据服务实例
        cqrs_bus: CQRS总线实例
    """
    # 注册命令处理器
    cqrs_bus.register_command_handler(
        ExecuteQueryCommand,
        ExecuteQueryCommandHandler(data_service)
    )
    cqrs_bus.register_command_handler(
        UpdateDataCommand,
        UpdateDataCommandHandler(data_service)
    )
    
    # 注册查询处理器
    cqrs_bus.register_query_handler(
        GetTableListQuery,
        GetTableListQueryHandler(data_service)
    )
    cqrs_bus.register_query_handler(
        GetTableDataQuery,
        GetTableDataQueryHandler(data_service)
    )
