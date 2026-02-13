#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存模块

提供查询结果缓存功能。
"""

from src.infrastructure.cache.cache_manager import (
    CacheManager,
    QueryCacheManager,
    get_query_cache
)

__all__ = ['CacheManager', 'QueryCacheManager', 'get_query_cache']
