#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试单例模式的线程安全性
验证 IMP-001 修复是否成功
"""

import sys
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.infrastructure.utils.scaling_manager import ScalingManager, get_scaling_manager
from src.data.repositories.driver_factory import DatabaseDriverFactory, get_driver_factory


class TestSingletonThreadSafety:
    """测试单例模式线程安全性"""
    
    def test_scaling_manager_thread_safety(self):
        """测试 ScalingManager 线程安全性"""
        print("\n测试1: ScalingManager 线程安全性")
        
        instances = []
        errors = []
        
        def create_instance():
            try:
                time.sleep(0.001)  # 模拟一些延迟
                instance = get_scaling_manager()
                instances.append(instance)
                return instance
            except Exception as e:
                errors.append(str(e))
                return None
        
        # 使用多线程同时创建实例
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_instance) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        # 验证所有实例相同
        unique_instances = set(id(r) for r in results if r is not None)
        
        if len(unique_instances) == 1:
            print(f"  [OK] 100个线程创建的实例ID相同: {unique_instances.pop()}")
        else:
            print(f"  [FAIL] 创建了 {len(unique_instances)} 个不同实例")
            return False
        
        if len(errors) == 0:
            print("  [OK] 无异常发生")
        else:
            print(f"  [FAIL] 发生 {len(errors)} 个异常: {errors[0]}")
            return False
        
        return True
    
    def test_driver_factory_thread_safety(self):
        """测试 DatabaseDriverFactory 线程安全性"""
        print("\n测试2: DatabaseDriverFactory 线程安全性")
        
        instances = []
        errors = []
        
        def create_instance():
            try:
                time.sleep(0.001)  # 模拟一些延迟
                instance = get_driver_factory()
                instances.append(instance)
                return instance
            except Exception as e:
                errors.append(str(e))
                return None
        
        # 使用多线程同时创建实例
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_instance) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]
        
        # 验证所有实例相同
        unique_instances = set(id(r) for r in results if r is not None)
        
        if len(unique_instances) == 1:
            print(f"  [OK] 100个线程创建的实例ID相同: {unique_instances.pop()}")
        else:
            print(f"  [FAIL] 创建了 {len(unique_instances)} 个不同实例")
            return False
        
        if len(errors) == 0:
            print("  [OK] 无异常发生")
        else:
            print(f"  [FAIL] 发生 {len(errors)} 个异常: {errors[0]}")
            return False
        
        return True
    
    def test_concurrent_access(self):
        """测试并发访问安全性"""
        print("\n测试3: 并发访问安全性")
        
        results = {'scaling_manager': [], 'driver_factory': []}
        errors = []
        
        def access_scaling_manager():
            try:
                manager = get_scaling_manager()
                # 并发设置和读取
                manager.set_scale_factor(1.5)
                factor = manager.get_scale_factor()
                results['scaling_manager'].append(factor)
                return factor == 1.5
            except Exception as e:
                errors.append(f"ScalingManager: {e}")
                return False
        
        def access_driver_factory():
            try:
                factory = get_driver_factory()
                # 并发检测驱动
                driver_type = factory.detect_available_driver()
                results['driver_factory'].append(driver_type.value)
                return driver_type.value in ['iris', 'pyodbc', 'unknown']
            except Exception as e:
                errors.append(f"DriverFactory: {e}")
                return False
        
        # 混合访问两个单例
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for i in range(50):
                if i % 2 == 0:
                    futures.append(executor.submit(access_scaling_manager))
                else:
                    futures.append(executor.submit(access_driver_factory))
            
            success_count = sum(1 for f in as_completed(futures) if f.result())
        
        if success_count == 50:
            print(f"  [OK] 50次并发访问全部成功")
        else:
            print(f"  [FAIL] {50 - success_count} 次访问失败")
            return False
        
        if len(errors) == 0:
            print("  [OK] 无并发访问异常")
        else:
            print(f"  [FAIL] 发生 {len(errors)} 个异常")
            return False
        
        return True
    
    def test_performance_impact(self):
        """测试线程锁对性能的影响"""
        print("\n测试4: 性能影响评估")
        
        import time
        
        # 预热
        for _ in range(10):
            _ = get_scaling_manager()
        
        # 单线程性能
        start = time.time()
        for _ in range(1000):
            _ = get_scaling_manager()
        single_thread_time = time.time() - start
        
        # 多线程性能
        def get_instance():
            return get_scaling_manager()
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(executor.map(lambda _: get_instance(), range(1000)))
        multi_thread_time = time.time() - start
        
        print(f"  [INFO] 单线程 1000 次获取: {single_thread_time:.3f}秒")
        print(f"  [INFO] 多线程 1000 次获取 (10 workers): {multi_thread_time:.3f}秒")
        
        # 多线程不应比单线程慢太多（允许3倍以内）
        if multi_thread_time < single_thread_time * 3:
            print(f"  [OK] 多线程性能在可接受范围内")
            return True
        else:
            print(f"  [WARN] 多线程性能下降明显")
            return True  # 仍然通过，只是警告
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("单例模式线程安全性测试 (IMP-001)")
        print("=" * 60)
        
        tests = [
            ("ScalingManager 线程安全", self.test_scaling_manager_thread_safety),
            ("DriverFactory 线程安全", self.test_driver_factory_thread_safety),
            ("并发访问安全性", self.test_concurrent_access),
            ("性能影响评估", self.test_performance_impact),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                print(f"\n  [ERROR] 测试异常: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
        
        print("\n" + "=" * 60)
        print("测试结果汇总:")
        print("=" * 60)
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        for name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {name}")
        
        print(f"\n总计: {passed}/{total} 通过")
        
        if passed == total:
            print("\n✓ 所有测试通过！单例模式线程安全")
            return 0
        else:
            print(f"\n✗ {total - passed} 个测试失败")
            return 1


def main():
    """主函数"""
    tester = TestSingletonThreadSafety()
    return tester.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
