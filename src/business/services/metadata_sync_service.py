#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
元数据同步服务

负责从数据库同步元数据到本地缓存
支持手动同步和自动定时同步
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from data.repositories.database_repository import DatabaseRepository
from business.services.metadata_cache_service import LocalMetadataCache

logger = logging.getLogger(__name__)


class MetadataSyncService:
    """
    元数据同步服务
    
    功能:
    - 从数据库读取表结构
    - 同步到本地元数据缓存
    - 支持增量更新和全量更新
    - 自动定时刷新
    """

    def __init__(self, 
                 db_repository: DatabaseRepository,
                 metadata_cache: LocalMetadataCache):
        """
        初始化同步服务
        
        Args:
            db_repository: 数据库仓库
            metadata_cache: 元数据缓存
        """
        self.db_repository = db_repository
        self.metadata_cache = metadata_cache
        self._last_sync_times: Dict[str, datetime] = {}

    def sync_metadata(self, connection_id: str, force_full: bool = False) -> bool:
        """
        同步元数据
        
        Args:
            connection_id: 连接标识符
            force_full: 是否强制全量更新
            
        Returns:
            同步是否成功
        """
        try:
            logger.info(f"Starting metadata sync for connection: {connection_id}")
            
            # 获取所有表
            tables = self.db_repository.get_all_tables()
            logger.info(f"Found {len(tables)} tables")
            
            # 获取每个表的列信息
            tables_data = []
            for table_name in tables:
                try:
                    columns = self.db_repository.get_table_columns(table_name)
                    
                    tables_data.append({
                        'name': table_name,
                        'type': 'TABLE',
                        'comment': '',  # 可以从数据库获取
                        'columns': [
                            {
                                'name': col['name'],
                                'type': col.get('type', 'VARCHAR'),
                                'nullable': col.get('nullable', True),
                                'default': col.get('default'),
                                'comment': col.get('comment', ''),
                                'position': col.get('ordinal_position', 0)
                            }
                            for col in columns
                        ]
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to get columns for table {table_name}: {e}")
                    # 继续处理其他表
            
            # 更新缓存
            self.metadata_cache.update_metadata(connection_id, tables_data)
            
            # 记录同步时间
            self._last_sync_times[connection_id] = datetime.now()
            
            logger.info(f"Metadata sync completed: {len(tables_data)} tables")
            return True
            
        except Exception as e:
            logger.error(f"Metadata sync failed: {e}", exc_info=True)
            return False

    def should_sync(self, connection_id: str, interval_minutes: int = 30) -> bool:
        """
        检查是否需要同步
        
        Args:
            connection_id: 连接标识符
            interval_minutes: 同步间隔（分钟）
            
        Returns:
            是否需要同步
        """
        last_sync = self._last_sync_times.get(connection_id)
        
        if last_sync is None:
            return True
        
        elapsed = datetime.now() - last_sync
        return elapsed > timedelta(minutes=interval_minutes)

    def get_last_sync_time(self, connection_id: str) -> Optional[datetime]:
        """
        获取上次同步时间
        
        Args:
            connection_id: 连接标识符
            
        Returns:
            上次同步时间，如果没有则返回 None
        """
        return self._last_sync_times.get(connection_id)

    def clear_sync_record(self, connection_id: str):
        """
        清除同步记录
        
        Args:
            connection_id: 连接标识符
        """
        if connection_id in self._last_sync_times:
            del self._last_sync_times[connection_id]


# 便捷函数
def create_metadata_sync_service(
    db_repository: DatabaseRepository,
    cache_path: str = 'data/metadata_cache.db'
) -> MetadataSyncService:
    """
    创建元数据同步服务实例
    
    Args:
        db_repository: 数据库仓库
        cache_path: 缓存数据库路径
        
    Returns:
        MetadataSyncService 实例
    """
    from business.services.metadata_cache_service import LocalMetadataCache
    
    cache = LocalMetadataCache(cache_path)
    return MetadataSyncService(db_repository, cache)
