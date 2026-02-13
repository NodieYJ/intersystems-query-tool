#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础仓库模块

提供Repository模式的基础抽象类和通用实现。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class BaseRepository(ABC):
    """
    基础仓库类
    
    所有实体仓库的基类，提供通用的CRUD操作接口。
    """
    
    def __init__(self, db_repository: Any):
        """
        初始化基础仓库
        
        Args:
            db_repository: 数据库仓库实例
        """
        self.db_repository = db_repository
    
    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[T]:
        """
        根据ID查找实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[T]: 找到的实体或None
        """
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        查找所有实体
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[T]: 实体列表
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> bool:
        """
        保存实体（新增或更新）
        
        Args:
            entity: 要保存的实体
            
        Returns:
            bool: 是否保存成功
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取实体总数
        
        Returns:
            int: 实体数量
        """
        pass
    
    def execute_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        return self.db_repository.execute_query(query, params)
    
    def execute_non_query(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> bool:
        """
        执行非查询操作
        
        Args:
            query: SQL语句
            params: 语句参数
            
        Returns:
            bool: 是否执行成功
        """
        return self.db_repository.execute_non_query(query, params)
    
    def execute_scalar(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> Any:
        """
        执行标量查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            Any: 查询结果
        """
        return self.db_repository.execute_scalar(query, params)


class QueryRepository(BaseRepository):
    """
    通用查询仓库
    
    提供通用的SQL查询执行功能。
    """
    
    def find_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """根据ID查找实体"""
        raise NotImplementedError("QueryRepository不支持此操作")
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """查找所有实体"""
        raise NotImplementedError("QueryRepository不支持此操作")
    
    def save(self, entity: Dict[str, Any]) -> bool:
        """保存实体"""
        raise NotImplementedError("QueryRepository不支持此操作")
    
    def delete(self, entity_id: Any) -> bool:
        """删除实体"""
        raise NotImplementedError("QueryRepository不支持此操作")
    
    def count(self) -> int:
        """获取实体总数"""
        raise NotImplementedError("QueryRepository不支持此操作")
    
    def query(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        执行SQL查询
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果
        """
        return self.execute_query(sql, params)
    
    def update(self, sql: str, params: Optional[List[Any]] = None) -> bool:
        """
        执行更新操作
        
        Args:
            sql: SQL更新语句
            params: 语句参数
            
        Returns:
            bool: 是否执行成功
        """
        return self.execute_non_query(sql, params)
