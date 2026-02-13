#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存管理模块

提供查询结果缓存功能，减少数据库访问。
支持TTL过期、LRU淘汰策略。
"""

import time
import hashlib
import logging
from typing import Any, Dict, List, Optional, Callable
from threading import RLock
from dataclasses import dataclass
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl
    
    def touch(self):
        """更新访问时间（用于LRU）"""
        self.timestamp = time.time()
        self.access_count += 1


class CacheManager:
    """
    缓存管理器
    
    提供基于内存的缓存功能，支持：
    - TTL过期
    - LRU淘汰
    - 线程安全
    - 统计信息
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,  # 5分钟
        enable_stats: bool = True
    ):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认过期时间（秒）
            enable_stats: 是否启用统计
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.enable_stats = enable_stats
        
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        
        # 统计信息
        if enable_stats:
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expirations': 0,
                'inserts': 0
            }
        
        logger.info(f"缓存管理器初始化完成: max_size={max_size}, default_ttl={default_ttl}s")
    
    def _generate_key(self, query: str, params: Optional[tuple] = None) -> str:
        """
        生成缓存键
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            str: 缓存键
        """
        key_string = f"{query}:{str(params)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            Any: 缓存值或默认值
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                if self.enable_stats:
                    self._stats['misses'] += 1
                return default
            
            if entry.is_expired():
                # 删除过期条目
                del self._cache[key]
                if self.enable_stats:
                    self._stats['expirations'] += 1
                    self._stats['misses'] += 1
                return default
            
            # 更新访问信息（LRU）
            entry.touch()
            self._cache.move_to_end(key)
            
            if self.enable_stats:
                self._stats['hits'] += 1
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            
        Returns:
            bool: 是否设置成功
        """
        ttl = ttl or self.default_ttl
        
        with self._lock:
            # 检查是否需要淘汰
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()
            
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl
            )
            
            self._cache[key] = entry
            self._cache.move_to_end(key)
            
            if self.enable_stats:
                self._stats['inserts'] += 1
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        删除缓存条目
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")
    
    def _evict_lru(self) -> None:
        """淘汰最久未使用的条目"""
        if self._cache:
            # OrderedDict的popitem(last=False)移除最早的条目
            oldest_key, _ = self._cache.popitem(last=False)
            if self.enable_stats:
                self._stats['evictions'] += 1
            logger.debug(f"LRU淘汰: {oldest_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'usage_percent': (len(self._cache) / self.max_size * 100),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'inserts': self._stats['inserts']
            }
    
    def cached(
        self,
        ttl: Optional[int] = None,
        key_prefix: str = ""
    ):
        """
        缓存装饰器
        
        Args:
            ttl: 过期时间
            key_prefix: 键前缀
            
        Returns:
            Callable: 装饰器函数
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
                cache_key = hashlib.md5(cache_key.encode()).hexdigest()
                
                # 尝试从缓存获取
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"缓存命中: {func.__name__}")
                    return cached_value
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 存入缓存
                self.set(cache_key, result, ttl)
                logger.debug(f"缓存存储: {func.__name__}")
                
                return result
            
            return wrapper
        return decorator


class QueryCacheManager(CacheManager):
    """
    查询缓存管理器
    
    专门用于缓存数据库查询结果。
    """
    
    def get_query_result(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> Optional[Any]:
        """
        获取查询结果缓存
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            Optional[Any]: 缓存的查询结果
        """
        key = self._generate_key(query, params)
        return self.get(key)
    
    def set_query_result(
        self,
        query: str,
        result: Any,
        params: Optional[tuple] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置查询结果缓存
        
        Args:
            query: SQL查询
            result: 查询结果
            params: 查询参数
            ttl: 过期时间
            
        Returns:
            bool: 是否设置成功
        """
        key = self._generate_key(query, params)
        return self.set(key, result, ttl)
    
    def invalidate_query(
        self,
        query: str,
        params: Optional[tuple] = None
    ) -> bool:
        """
        使查询缓存失效
        
        Args:
            query: SQL查询
            params: 查询参数
            
        Returns:
            bool: 是否删除成功
        """
        key = self._generate_key(query, params)
        return self.delete(key)
    
    def invalidate_table(self, table_name: str) -> int:
        """
        使与表相关的所有缓存失效
        
        Args:
            table_name: 表名
            
        Returns:
            int: 失效的缓存数量
        """
        with self._lock:
            keys_to_delete = [
                key for key, entry in self._cache.items()
                if table_name.lower() in str(entry.value).lower()
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            logger.info(f"表 {table_name} 相关缓存已失效: {len(keys_to_delete)} 条")
            return len(keys_to_delete)


# 全局缓存实例
_query_cache: Optional[QueryCacheManager] = None


def get_query_cache(
    max_size: int = 1000,
    default_ttl: int = 300
) -> QueryCacheManager:
    """
    获取查询缓存管理器实例
    
    Args:
        max_size: 最大缓存条目数
        default_ttl: 默认过期时间
        
    Returns:
        QueryCacheManager: 缓存管理器实例
    """
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCacheManager(max_size, default_ttl)
    return _query_cache
