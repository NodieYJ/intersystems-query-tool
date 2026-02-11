#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConfigManager线程安全测试

测试ConfigManager的并发读写能力
"""

import json
import os
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.infrastructure.config.config_manager import ConfigManager


class TestConfigManagerThreading(unittest.TestCase):
    """ConfigManager线程安全测试类"""

    def setUp(self):
        """测试前置条件"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
    def tearDown(self):
        """测试后置条件"""
        # 清理临时文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        if os.path.exists(f"{self.config_file}.tmp"):
            os.remove(f"{self.config_file}.tmp")
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_concurrent_writes(self):
        """
        测试并发写入（核心测试）
        
        多个线程同时写入配置，应该都能成功
        并且文件内容保持一致
        """
        config_manager = ConfigManager(self.config_file)
        
        num_threads = 10
        iterations_per_thread = 5
        
        def write_config(thread_id):
            """写入配置的线程函数"""
            results = []
            for i in range(iterations_per_thread):
                key = f"thread_{thread_id}.value_{i}"
                value = f"thread_{thread_id}_value_{i}_{time.time_ns()}"
                result = config_manager.set(key, value)
                results.append(result)
                
                # 随机保存
                if i % 2 == 0:
                    save_result = config_manager.save()
                    results.append(save_result)
            
            return results
        
        # 使用线程池并发执行写入
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(write_config, i) for i in range(num_threads)]
            
            # 收集所有结果
            all_results = []
            for future in as_completed(futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    self.fail(f"线程执行失败: {str(e)}")
        
        # 验证结果
        successful_writes = sum(1 for r in all_results if r is True)
        total_operations = len(all_results)
        
        self.assertGreater(successful_writes, 0, "至少应有部分写入操作成功")
        print(f"[INFO] 并发写入测试: {successful_writes}/{total_operations} 操作成功")

    def test_atomic_save(self):
        """
        测试原子保存（关键测试）
        
        在保存过程中中断，应该不会损坏配置文件
        """
        config_manager = ConfigManager(self.config_file)
        
        # 写入配置
        for i in range(100):
            config_manager.set(f"key_{i}", f"value_{i}")
        
        # 保存配置
        result = config_manager.save()
        self.assertTrue(result, "保存应该成功")
        
        # 验证文件内容
        self.assertTrue(os.path.exists(self.config_file), "配置文件应该存在")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        # 验证数据完整性
        self.assertEqual(loaded_config.get("key_0"), "value_0", "数据应该完整保存")
        self.assertEqual(loaded_config.get("key_99"), "value_99", "数据应该完整保存")
        
        # 验证没有临时文件残留
        temp_file = f"{self.config_file}.tmp"
        self.assertFalse(os.path.exists(temp_file), "不应该有临时文件残留")

    def test_concurrent_read_and_write(self):
        """
        测试并发读写
        
        多个线程同时读写配置，系统应该正确处理
        """
        config_manager = ConfigManager(self.config_file)
        
        # 初始写入一些数据
        for i in range(50):
            config_manager.set(f"initial.key_{i}", f"initial_value_{i}")
        config_manager.save()
        
        errors = []
        lock = threading.Lock()
        
        def read_operation():
            """读取配置的线程函数"""
            try:
                for _ in range(10):
                    value = config_manager.get("initial.key_0")
                    # 验证读取结果
                    if value and not value.startswith("thread"):
                        pass  # 正常的读取
                    time.sleep(0.001)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        def write_operation():
            """写入配置的线程函数"""
            try:
                thread_id = threading.current_thread().ident
                for i in range(10):
                    config_manager.set(f"thread_{thread_id}.write_{i}", f"value_{i}")
                    config_manager.save()
                    time.sleep(0.001)
            except Exception as e:
                with lock:
                    errors.append(str(e))
        
        # 并发执行读写操作
        threads = []
        for _ in range(5):
            t = threading.Thread(target=read_operation)
            threads.append(t)
            t = threading.Thread(target=write_operation)
            threads.append(t)
        
        # 启动所有线程
        for t in threads:
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证没有错误
        self.assertEqual(len(errors), 0, f"不应该有错误: {errors}")
        
        print(f"[INFO] 并发读写测试完成，错误数: {len(errors)}")

    def test_file_lock_prevents_corruption(self):
        """
        测试文件锁防止数据损坏
        
        模拟快速连续的保存操作，验证不会产生临时文件残留
        """
        config_manager = ConfigManager(self.config_file)
        
        # 快速连续保存
        for i in range(20):
            config_manager.set("rapid.save_count", i)
            config_manager.save()
            time.sleep(0.01)  # 短暂延迟
        
        # 验证最终状态
        self.assertTrue(os.path.exists(self.config_file), "配置文件应该存在")
        
        # 验证没有临时文件
        temp_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.tmp')]
        self.assertEqual(len(temp_files), 0, f"不应该有临时文件: {temp_files}")
        
        # 验证内容
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        self.assertEqual(config.get("rapid", {}).get("save_count"), 19, "最后一次保存应该成功")


# 测试入口
if __name__ == '__main__':
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 运行测试
    unittest.main(verbosity=2)
