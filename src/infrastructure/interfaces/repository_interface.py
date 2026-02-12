#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据仓库接口定义模块

定义所有数据仓库需要实现的接口，包括：
- 基本CRUD操作
- 批量操作
- 事务支持
- 连接管理
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar('T')


class IRepository(ABC, Generic[T]):
    """
    数据仓库接口基类
    
    定义数据访问层的基本操作，所有具体仓库实现都应该继承此接口。
    
    类型参数:
        T: 实体类型
        
    示例:
        >>> class UserRepository(IRepository[User]):
        ...     def get_by_id(self, id: int) -> Optional[User]:
        ...         pass
    """
    
    @abstractmethod
    def get_by_id(self, id: Union[int, str]) -> Optional[T]:
        """
        根据ID获取实体
        
        Args:
            id: 实体唯一标识符
            
        Returns:
            Optional[T]: 找到的实体，不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """
        获取所有实体
        
        Returns:
            List[T]: 实体列表
        """
        pass
    
    @abstractmethod
    def find(self, **criteria: Any) -> List[T]:
        """
        根据条件查询实体
        
        Args:
            **criteria: 查询条件，如 name="test", status=1
            
        Returns:
            List[T]: 符合条件的实体列表
        """
        pass
    
    @abstractmethod
    def find_one(self, **criteria: Any) -> Optional[T]:
        """
        根据条件查询单个实体
        
        Args:
            **criteria: 查询条件
            
        Returns:
            Optional[T]: 找到的第一个实体，不存在则返回None
        """
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        创建新实体
        
        Args:
            entity: 要创建的实体
            
        Returns:
            T: 创建后的实体（包含生成的ID等）
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        更新实体
        
        Args:
            entity: 要更新的实体
            
        Returns:
            T: 更新后的实体
        """
        pass
    
    @abstractmethod
    def delete(self, id: Union[int, str]) -> bool:
        """
        删除实体
        
        Args:
            id: 实体唯一标识符
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    def exists(self, id: Union[int, str]) -> bool:
        """
        检查实体是否存在
        
        Args:
            id: 实体唯一标识符
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count(self, **criteria: Any) -> int:
        """
        统计符合条件的实体数量
        
        Args:
            **criteria: 查询条件，为空则统计所有
            
        Returns:
            int: 实体数量
        """
        pass


class IQueryRepository(ABC):
    """
    查询仓库接口
    
    专门用于SQL查询操作的仓库接口，支持执行查询和获取结果。
    
    示例:
        >>> repo = QueryRepository()
        >>> results = repo.execute_query("SELECT * FROM users WHERE age > ?", [18])
    """
    
    @abstractmethod
    def execute_query(
        self, 
        sql: str, 
        parameters: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行查询SQL
        
        Args:
            sql: SQL查询语句
            parameters: 查询参数列表（用于参数化查询）
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表，每条记录为字典
            
        Raises:
            DatabaseException: 查询执行失败
        """
        pass
    
    @abstractmethod
    def execute_non_query(
        self, 
        sql: str, 
        parameters: Optional[List[Any]] = None
    ) -> int:
        """
        执行非查询SQL（INSERT, UPDATE, DELETE）
        
        Args:
            sql: SQL语句
            parameters: 参数列表
            
        Returns:
            int: 受影响的行数
            
        Raises:
            DatabaseException: 执行失败
        """
        pass
    
    @abstractmethod
    def execute_scalar(
        self, 
        sql: str, 
        parameters: Optional[List[Any]] = None
    ) -> Any:
        """
        执行查询并返回单个值
        
        Args:
            sql: SQL语句
            parameters: 参数列表
            
        Returns:
            Any: 查询结果的第一个值
            
        Raises:
            DatabaseException: 查询执行失败
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """
        获取连接信息
        
        Returns:
            Dict[str, Any]: 连接信息字典
        """
        pass


class ITransactionRepository(IRepository[T], ABC):
    """
    支持事务的仓库接口
    
    继承自IRepository，增加事务支持能力。
    
    示例:
        >>> with repo.transaction() as tx:
        ...     repo.create(entity1)
        ...     repo.create(entity2)
        ...     tx.commit()
    """
    
    @abstractmethod
    def begin_transaction(self) -> 'ITransactionContext':
        """
        开始事务
        
        Returns:
            ITransactionContext: 事务上下文
        """
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """提交事务"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """回滚事务"""
        pass


class ITransactionContext(ABC):
    """
    事务上下文接口
    
    用于with语句管理事务生命周期。
    """
    
    @abstractmethod
    def __enter__(self) -> 'ITransactionContext':
        """进入事务上下文"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """退出事务上下文，自动提交或回滚"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """提交事务"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """回滚事务"""
        pass
