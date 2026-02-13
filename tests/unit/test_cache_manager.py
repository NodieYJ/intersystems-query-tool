#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存管理器单元测试

测试 CacheManager 和 QueryCacheManager 功能
"""

import unittest
import time
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.infrastructure.cache.cache_manager import (
    CacheManager,
    QueryCacheManager,
    CacheEntry,
    get_query_cache
)


class TestCacheEntry(unittest.TestCase):
    """缓存条目测试类"""
    
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(
            key='test_key',
            value='test_value',
            timestamp=time.time(),
            ttl=60
        )
        
        self.assertEqual(entry.key, 'test_key')
        self.assertEqual(entry.value, 'test_value')
        self.assertFalse(entry.is_expired())
    
    def test_cache_entry_expiration(self):
        """测试缓存条目过期"""
        entry = CacheEntry(
            key='test_key',
            value='test_value',
            timestamp=time.time() - 61,  # 61秒前
            ttl=60
        )
        
        self.assertTrue(entry.is_expired())
    
    def test_cache_entry_touch(self):
        """测试缓存条目访问更新"""
        entry = CacheEntry(
            key='test_key',
            value='test_value',
            timestamp=time.time(),
            ttl=60
        )
        
        old_timestamp = entry.timestamp
        time.sleep(0.01)
        entry.touch()
        
        self.assertGreater(entry.timestamp, old_timestamp)
        self.assertEqual(entry.access_count, 1)


class TestCacheManager(unittest.TestCase):
    """缓存管理器测试类"""
    
    def setUp(self):
        """测试准备"""
        self.cache = CacheManager(max_size=100, default_ttl=60)
    
    def tearDown(self):
        """测试清理"""
        self.cache.clear()
    
    def test_basic_get_set(self):
        """测试基本获取和设置"""
        # 设置缓存
        self.cache.set('key1', 'value1')
        
        # 获取缓存
        value = self.cache.get('key1')
        self.assertEqual(value, 'value1')
    
    def test_get_nonexistent(self):
        """测试获取不存在的键"""
        value = self.cache.get('nonexistent')
        self.assertIsNone(value)
    
    def test_get_with_default(self):
        """测试获取带默认值"""
        value = self.cache.get('nonexistent', default='default_value')
        self.assertEqual(value, 'default_value')
    
    def test_ttl_expiration(self):
        """测试TTL过期"""
        # 设置1秒过期的缓存
        self.cache.set('key1', 'value1', ttl=1)
        
        # 立即获取应该存在
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # 等待2秒
        time.sleep(2)
        
        # 再次获取应该过期
        self.assertIsNone(self.cache.get('key1'))
    
    def test_lru_eviction(self):
        """测试LRU淘汰"""
        # 创建小容量缓存
        small_cache = CacheManager(max_size=3, default_ttl=60)
        
        # 添加3个条目
        small_cache.set('key1', 'value1')
        small_cache.set('key2', 'value2')
        small_cache.set('key3', 'value3')
        
        # 访问key1，使其成为最近使用
        small_cache.get('key1')
        
        # 添加第4个条目，应该淘汰key2（最久未使用）
        small_cache.set('key4', 'value4')
        
        # key1应该存在
        self.assertIsNotNone(small_cache.get('key1'))
        # key2应该被淘汰
        self.assertIsNone(small_cache.get('key2'))
    
    def test_delete(self):
        """测试删除"""
        self.cache.set('key1', 'value1')
        
        # 删除存在的键
        result = self.cache.delete('key1')
        self.assertTrue(result)
        self.assertIsNone(self.cache.get('key1'))
        
        # 删除不存在的键
        result = self.cache.delete('nonexistent')
        self.assertFalse(result)
    
    def test_clear(self):
        """测试清空"""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        self.cache.clear()
        
        self.assertIsNone(self.cache.get('key1'))
        self.assertIsNone(self.cache.get('key2'))
    
    def test_stats(self):
        """测试统计信息"""
        # 设置并获取
        self.cache.set('key1', 'value1')
        self.cache.get('key1')  # 命中
        self.cache.get('nonexistent')  # 未命中
        
        stats = self.cache.get_stats()
        
        self.assertIn('size', stats)
        self.assertIn('hits', stats)
        self.assertIn('misses', stats)
        self.assertIn('hit_rate', stats)
        
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
    
    def test_complex_value(self):
        """测试复杂值类型"""
        complex_value = {
            'id': 1,
            'name': 'test',
            'items': [1, 2, 3]
        }
        
        self.cache.set('complex', complex_value)
        retrieved = self.cache.get('complex')
        
        self.assertEqual(retrieved, complex_value)


class TestQueryCacheManager(unittest.TestCase):
    """查询缓存管理器测试类"""
    
    def setUp(self):
        """测试准备"""
        self.cache = QueryCacheManager(max_size=100, default_ttl=60)
    
    def tearDown(self):
        """测试清理"""
        self.cache.clear()
    
    def test_query_result_cache(self):
        """测试查询结果缓存"""
        query = "SELECT * FROM users"
        result = [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
        
        # 设置缓存
        self.cache.set_query_result(query, result)
        
        # 获取缓存
        cached = self.cache.get_query_result(query)
        self.assertEqual(cached, result)
    
    def test_query_result_with_params(self):
        """测试带参数的查询缓存"""
        query = "SELECT * FROM users WHERE id = %s"
        params = (1,)
        result = [{'id': 1, 'name': 'Alice'}]
        
        # 设置缓存
        self.cache.set_query_result(query, result, params)
        
        # 使用相同参数获取
        cached = self.cache.get_query_result(query, params)
        self.assertEqual(cached, result)
        
        # 使用不同参数获取应该为None
        different_cached = self.cache.get_query_result(query, (2,))
        self.assertIsNone(different_cached)
    
    def test_invalidate_query(self):
        """测试使查询缓存失效"""
        query = "SELECT * FROM users"
        result = [{'id': 1}]
        
        self.cache.set_query_result(query, result)
        self.assertIsNotNone(self.cache.get_query_result(query))
        
        # 使缓存失效
        self.cache.invalidate_query(query)
        
        # 再次获取应该为None
        self.assertIsNone(self.cache.get_query_result(query))
    
    def test_invalidate_table(self):
        """测试使表相关缓存失效"""
        # 设置多个表相关的缓存
        self.cache.set_query_result("SELECT * FROM users WHERE id = 1", [{'table': 'users', 'id': 1}])
        self.cache.set_query_result("SELECT * FROM orders WHERE id = 100", [{'table': 'orders', 'id': 100}])
        self.cache.set_query_result("SELECT * FROM products WHERE id = 10", [{'table': 'products', 'id': 10}])
        
        # 使users表相关缓存失效
        count = self.cache.invalidate_table('users')
        
        # 应该至少失效1条
        self.assertGreaterEqual(count, 1)
    
    def test_global_instance(self):
        """测试全局单例"""
        cache1 = get_query_cache()
        cache2 = get_query_cache()
        
        self.assertIs(cache1, cache2)


class TestCacheDecorator(unittest.TestCase):
    """缓存装饰器测试类"""
    
    def setUp(self):
        """测试准备"""
        self.cache = CacheManager(max_size=100, default_ttl=60)
        self.call_count = 0
    
    def tearDown(self):
        """测试清理"""
        self.cache.clear()
    
    def test_cached_decorator(self):
        """测试缓存装饰器"""
        @self.cache.cached(ttl=60)
        def expensive_function(x):
            self.call_count += 1
            return x * x
        
        # 第一次调用
        result1 = expensive_function(5)
        self.assertEqual(result1, 25)
        self.assertEqual(self.call_count, 1)
        
        # 第二次调用相同参数，应该使用缓存
        result2 = expensive_function(5)
        self.assertEqual(result2, 25)
        self.assertEqual(self.call_count, 1)  # 不应该增加
        
        # 不同参数应该重新计算
        result3 = expensive_function(10)
        self.assertEqual(result3, 100)
        self.assertEqual(self.call_count, 2)


if __name__ == '__main__':
    unittest.main()
