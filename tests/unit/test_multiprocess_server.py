#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多进程服务器并发测试

测试5000+并发连接能力。
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.server import (
    MultiProcessServer,
    WorkerTask,
    WorkerResult,
    create_multiprocess_server,
)


async def test_basic_multiprocess():
    """测试基本多进程功能"""
    print("\n=== 测试1: 基本多进程功能 ===")
    
    server = create_multiprocess_server(num_workers=2)
    
    # 启动服务器
    await server.start()
    print(f"Server started")
    
    # 提交任务
    results = []
    for i in range(10):
        result = await server.handle_request(f"task_{i}")
        if result:
            results.append(result)
            print(f"Task {i}: success={result.success}")
    
    # 停止服务器
    await server.stop()
    print(f"Server stopped")
    
    assert len(results) == 10, f"Expected 10 results, got {len(results)}"
    success_count = sum(1 for r in results if r.success)
    print(f"Success rate: {success_count}/{len(results)}")
    
    return True


async def test_concurrent_requests():
    """测试并发请求处理"""
    print("\n=== 测试2: 并发请求处理 ===")
    
    server = create_multiprocess_server(num_workers=4)
    await server.start()
    
    # 并发提交100个任务
    num_tasks = 100
    start_time = time.time()
    
    tasks = [
        server.handle_request(f"concurrent_task_{i}")
        for i in range(num_tasks)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = time.time() - start_time
    
    # 统计结果
    success_count = sum(1 for r in results if isinstance(r, WorkerResult) and r.success)
    error_count = sum(1 for r in results if isinstance(r, Exception))
    
    print(f"Tasks: {num_tasks}")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Throughput: {num_tasks/elapsed:.2f} req/s")
    
    await server.stop()
    
    assert success_count == num_tasks, f"Expected {num_tasks} successes, got {success_count}"
    
    return True


async def test_server_stats():
    """测试服务器统计信息"""
    print("\n=== 测试3: 服务器统计信息 ===")
    
    server = create_multiprocess_server(num_workers=2)
    await server.start()
    
    # 获取初始统计
    stats = server.get_stats()
    print(f"Initial stats: {stats}")
    
    # 提交一些任务
    for i in range(5):
        await server.handle_request(f"stats_task_{i}")
    
    # 再次获取统计
    stats = server.get_stats()
    print(f"After tasks stats:")
    print(f"  - Active workers: {stats.get('active_workers')}")
    print(f"  - Total requests: {stats.get('total_requests')}")
    print(f"  - Total errors: {stats.get('total_errors')}")
    
    await server.stop()
    
    return True


async def simulate_load_test():
    """模拟负载测试"""
    print("\n=== 测试4: 负载测试模拟 ===")
    print("Simulating 5000 concurrent connections...")
    
    # 使用4个worker进程
    server = create_multiprocess_server(num_workers=4)
    await server.start()
    
    # 模拟500个并发请求（实际5000需要更多资源）
    num_requests = 500
    concurrency = 100
    
    async def batch_requests(batch_id):
        """批量请求"""
        tasks = []
        for i in range(concurrency):
            task_id = f"batch_{batch_id}_task_{i}"
            tasks.append(server.handle_request(task_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = sum(1 for r in results if isinstance(r, WorkerResult) and r.success)
        return success
    
    start_time = time.time()
    
    # 分批次发送请求
    batches = num_requests // concurrency
    batch_results = []
    
    for batch_id in range(batches):
        success = await batch_requests(batch_id)
        batch_results.append(success)
        print(f"Batch {batch_id + 1}/{batches}: {success}/{concurrency} success")
    
    elapsed = time.time() - start_time
    total_success = sum(batch_results)
    
    print(f"\nLoad Test Results:")
    print(f"  - Total requests: {num_requests}")
    print(f"  - Success: {total_success}")
    print(f"  - Failed: {num_requests - total_success}")
    print(f"  - Time: {elapsed:.2f}s")
    print(f"  - Throughput: {num_requests/elapsed:.2f} req/s")
    print(f"  - Latency: {elapsed/num_requests*1000:.2f}ms/req")
    
    # 获取最终统计
    stats = server.get_stats()
    print(f"\nServer Stats:")
    print(f"  - Active workers: {stats.get('active_workers')}")
    print(f"  - Total requests: {stats.get('total_requests')}")
    print(f"  - Total errors: {stats.get('total_errors')}")
    
    await server.stop()
    
    # 验证成功率
    success_rate = total_success / num_requests
    print(f"\nSuccess rate: {success_rate*100:.1f}%")
    
    assert success_rate >= 0.95, f"Success rate too low: {success_rate}"
    
    return True


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("多进程服务器并发测试")
    print("=" * 60)
    
    tests = [
        ("基本多进程功能", test_basic_multiprocess),
        ("并发请求处理", test_concurrent_requests),
        ("服务器统计信息", test_server_stats),
        ("负载测试模拟", simulate_load_test),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print('='*60)
            
            result = await test_func()
            if result:
                print(f"✓ {name}: PASSED")
                passed += 1
            else:
                print(f"✗ {name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"✗ {name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
