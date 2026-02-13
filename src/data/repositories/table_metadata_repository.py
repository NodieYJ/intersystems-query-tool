#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表元数据仓库模块

提供数据库表结构信息的查询操作。
"""

from typing import Any, Dict, List, Optional

from src.data.repositories.base_repository import BaseRepository


class TableMetadataRepository(BaseRepository):
    """
    表元数据仓库
    
    管理数据库表结构信息的查询。
    """
    
    def __init__(self, db_repository: Any):
        """
        初始化表元数据仓库
        
        Args:
            db_repository: 数据库仓库实例
        """
        super().__init__(db_repository)
    
    def get_all_tables(self) -> List[str]:
        """
        获取所有表名
        
        Returns:
            List[str]: 表名列表
        """
        # IRIS/Cache数据库查询
        query = "SELECT name FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        result = self.execute_query(query)
        return [row.get('name', row.get('TABLE_NAME', '')) for row in result]
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表的列信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict[str, Any]]: 列信息列表
        """
        query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query, [table_name])
    
    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表的索引信息
        
        Args:
            table_name: 表名
            
        Returns:
            List[Dict[str, Any]]: 索引信息列表
        """
        query = """
            SELECT 
                INDEX_NAME,
                COLUMN_NAME,
                NON_UNIQUE
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """
        return self.execute_query(query, [table_name])
    
    def get_table_primary_key(self, table_name: str) -> Optional[str]:
        """
        获取表的主键列名
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[str]: 主键列名或None
        """
        query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_NAME = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
            LIMIT 1
        """
        result = self.execute_query(query, [table_name])
        return result[0].get('COLUMN_NAME') if result else None
    
    def get_table_row_count(self, table_name: str) -> int:
        """
        获取表的记录数
        
        Args:
            table_name: 表名
            
        Returns:
            int: 记录数
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.execute_scalar(query)
        return result if result else 0
    
    def get_table_sample_data(
        self,
        table_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取表的样本数据
        
        Args:
            table_name: 表名
            limit: 样本数量
            
        Returns:
            List[Dict[str, Any]]: 样本数据列表
        """
        query = f"SELECT TOP {limit} * FROM {table_name}"
        return self.execute_query(query)
    
    def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 是否存在
        """
        query = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = %s
        """
        result = self.execute_scalar(query, [table_name])
        return result > 0 if result else False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库信息
        
        Returns:
            Dict[str, Any]: 数据库信息字典
        """
        tables = self.get_all_tables()
        total_rows = sum(
            self.get_table_row_count(table)
            for table in tables[:10]  # 只统计前10张表，避免太慢
        )
        
        return {
            'table_count': len(tables),
            'tables': tables[:20],  # 只返回前20个表名
            'sample_total_rows': total_rows
        }
    
    # 抽象方法实现（此仓库只读）
    def find_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """不支持此操作"""
        raise NotImplementedError("TableMetadataRepository不支持此操作")
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """不支持此操作"""
        raise NotImplementedError("TableMetadataRepository不支持此操作")
    
    def save(self, entity: Dict[str, Any]) -> bool:
        """不支持此操作"""
        raise NotImplementedError("TableMetadataRepository为只读仓库")
    
    def delete(self, entity_id: Any) -> bool:
        """不支持此操作"""
        raise NotImplementedError("TableMetadataRepository为只读仓库")
    
    def count(self) -> int:
        """获取表数量"""
        return len(self.get_all_tables())
