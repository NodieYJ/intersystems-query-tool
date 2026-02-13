#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
查询历史仓库模块

提供查询历史记录的CRUD操作。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.data.repositories.base_repository import BaseRepository


class QueryHistoryRepository(BaseRepository):
    """
    查询历史仓库
    
    管理查询历史记录的增删改查操作。
    """
    
    TABLE_NAME = "query_history"
    
    def __init__(self, db_repository: Any):
        """
        初始化查询历史仓库
        
        Args:
            db_repository: 数据库仓库实例
        """
        super().__init__(db_repository)
    
    def find_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID查找查询历史记录
        
        Args:
            entity_id: 记录ID
            
        Returns:
            Optional[Dict[str, Any]]: 查询历史记录或None
        """
        query = f"SELECT * FROM {self.TABLE_NAME} WHERE id = %s"
        result = self.execute_query(query, [entity_id])
        return result[0] if result else None
    
    def find_all(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查找所有查询历史记录
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 查询历史记录列表
        """
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return self.execute_query(query, [limit, offset])
    
    def find_by_status(
        self,
        status: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        根据状态查找查询历史记录
        
        Args:
            status: 状态（success/failed）
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 查询历史记录列表
        """
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE status = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return self.execute_query(query, [status, limit])
    
    def search(
        self,
        keyword: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索查询历史记录
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 查询历史记录列表
        """
        query = f"""
            SELECT * FROM {self.TABLE_NAME}
            WHERE query_text LIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        return self.execute_query(query, [f"%{keyword}%", limit])
    
    def save(self, entity: Dict[str, Any]) -> bool:
        """
        保存查询历史记录
        
        Args:
            entity: 查询历史记录实体
            
        Returns:
            bool: 是否保存成功
        """
        if 'id' in entity and entity['id']:
            return self._update(entity)
        else:
            return self._insert(entity)
    
    def _insert(self, entity: Dict[str, Any]) -> bool:
        """
        插入新记录
        
        Args:
            entity: 实体数据
            
        Returns:
            bool: 是否插入成功
        """
        query = f"""
            INSERT INTO {self.TABLE_NAME}
            (query_text, params, status, execution_time, row_count, error_message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            entity.get('query_text', ''),
            entity.get('params', ''),
            entity.get('status', 'success'),
            entity.get('execution_time', 0),
            entity.get('row_count', 0),
            entity.get('error_message', ''),
            entity.get('created_at', datetime.now())
        ]
        return self.execute_non_query(query, params)
    
    def _update(self, entity: Dict[str, Any]) -> bool:
        """
        更新记录
        
        Args:
            entity: 实体数据
            
        Returns:
            bool: 是否更新成功
        """
        query = f"""
            UPDATE {self.TABLE_NAME}
            SET query_text = %s,
                params = %s,
                status = %s,
                execution_time = %s,
                row_count = %s,
                error_message = %s
            WHERE id = %s
        """
        params = [
            entity.get('query_text', ''),
            entity.get('params', ''),
            entity.get('status', 'success'),
            entity.get('execution_time', 0),
            entity.get('row_count', 0),
            entity.get('error_message', ''),
            entity['id']
        ]
        return self.execute_non_query(query, params)
    
    def delete(self, entity_id: int) -> bool:
        """
        删除查询历史记录
        
        Args:
            entity_id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        query = f"DELETE FROM {self.TABLE_NAME} WHERE id = %s"
        return self.execute_non_query(query, [entity_id])
    
    def delete_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """
        删除日期范围内的记录
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            int: 删除的记录数
        """
        query = f"""
            DELETE FROM {self.TABLE_NAME}
            WHERE created_at BETWEEN %s AND %s
        """
        # 返回受影响的行数
        return self.execute_non_query(query, [start_date, end_date])
    
    def clear_all(self) -> bool:
        """
        清空所有查询历史记录
        
        Returns:
            bool: 是否清空成功
        """
        query = f"DELETE FROM {self.TABLE_NAME}"
        return self.execute_non_query(query)
    
    def count(self) -> int:
        """
        获取查询历史记录总数
        
        Returns:
            int: 记录数量
        """
        query = f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
        result = self.execute_scalar(query)
        return result if result else 0
    
    def count_by_status(self, status: str) -> int:
        """
        根据状态统计记录数
        
        Args:
            status: 状态
            
        Returns:
            int: 记录数量
        """
        query = f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE status = %s"
        result = self.execute_scalar(query, [status])
        return result if result else 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        total = self.count()
        success = self.count_by_status('success')
        failed = self.count_by_status('failed')
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': (success / total * 100) if total > 0 else 0
        }
