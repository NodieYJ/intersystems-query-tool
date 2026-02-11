#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能测试脚本

测试关键功能的性能指标
"""

import time
import sys
import os

# 添加项目路径
sys.path.insert(0, 'D:\\pywindows')

from src.infrastructure.security.security_utils import SecurityUtils
from src.infrastructure.config.config_manager import ConfigManager
from src.business.services.query_history_manager import QueryHistoryManager
from src.business.services.data_analysis_service import DataAnalysisService

def test_security_performance():
    """测试安全功能性能"""
    print("\n=== 安全功能性能测试 ===")
    
    security = SecurityUtils()
    
    # 测试密码加密性能
    test_password = "TestPassword123!@#"
    iterations = 100
    
    start = time.time()
    for _ in range(iterations):
        security.encrypt_password(test_password)
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000  # 毫秒
    print(f"密码加密 ({iterations}次): 总时间 {elapsed:.3f}s, 平均 {avg_time:.2f}ms/次")
    
    # 测试密码验证性能
    encrypted = security.encrypt_password(test_password)
    
    start = time.time()
    for _ in range(iterations):
        security.verify_password(test_password, encrypted)
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000
    print(f"密码验证 ({iterations}次): 总时间 {elapsed:.3f}s, 平均 {avg_time:.2f}ms/次")
    
    return avg_time < 100  # 期望每次操作 < 100ms

def test_config_performance():
    """测试配置管理性能"""
    print("\n=== 配置管理性能测试 ===")
    
    iterations = 100
    
    # 测试配置获取
    start = time.time()
    for _ in range(iterations):
        config = ConfigManager("config.json")
        _ = config.get("database.server")
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000
    print(f"配置获取 ({iterations}次): 平均 {avg_time:.2f}ms/次")
    
    return avg_time < 10  # 期望 < 10ms

def test_query_history_performance():
    """测试查询历史性能"""
    print("\n=== 查询历史性能测试 ===")
    
    history_manager = QueryHistoryManager()
    
    # 预添加一些历史记录
    for i in range(50):
        history_manager.add_history(
            sql=f"SELECT * FROM table_{i} WHERE id = {i}",
            execution_time_ms=10 + i,
            row_count=i * 10
        )
    
    iterations = 100
    
    # 测试历史获取
    start = time.time()
    for _ in range(iterations):
        history_manager.get_history()
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000
    print(f"历史获取 ({iterations}次): 平均 {avg_time:.2f}ms/次")
    
    # 测试历史搜索
    start = time.time()
    for _ in range(iterations):
        history_manager.search_history("table_25")
    elapsed = time.time() - start
    
    avg_time = (elapsed / iterations) * 1000
    print(f"历史搜索 ({iterations}次): 平均 {avg_time:.2f}ms/次")
    
    # 清理
    history_manager.clear_history()
    
    return avg_time < 50  # 期望 < 50ms

def test_data_analysis_performance():
    """测试数据分析性能"""
    print("\n=== 数据分析性能测试 ===")
    
    import pandas as pd
    import numpy as np
    
    # 创建测试数据
    np.random.seed(42)
    n_rows = 10000
    n_cols = 20
    
    data = {
        f'col_{i}': np.random.randn(n_rows) if i % 3 == 0 else [f'value_{j % 100}' for j in range(n_rows)]
        for i in range(n_cols)
    }
    df = pd.DataFrame(data)
    
    service = DataAnalysisService()
    
    # 测试数据加载
    start = time.time()
    service.load_from_dataframe(df)
    elapsed = time.time() - start
    print(f"数据加载 ({n_rows}行 x {n_cols}列): {elapsed:.3f}s")
    
    # 测试统计计算
    start = time.time()
    stats = service.calculate_statistics()
    elapsed = time.time() - start
    print(f"统计计算: {elapsed:.3f}s")
    
    # 测试数据预览
    start = time.time()
    preview = service.get_data_preview(n_rows=100)
    elapsed = time.time() - start
    print(f"数据预览: {elapsed:.3f}s")
    
    service.clear()
    
    return elapsed < 1  # 期望预览 < 1s

def main():
    """主测试函数"""
    print("=" * 50)
    print("性能测试开始")
    print("=" * 50)
    
    results = {}
    
    # 运行各项测试
    results['security'] = test_security_performance()
    results['config'] = test_config_performance()
    results['query_history'] = test_query_history_performance()
    results['data_analysis'] = test_data_analysis_performance()
    
    # 输出结果摘要
    print("\n" + "=" * 50)
    print("性能测试结果摘要")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("All performance tests passed!")
    else:
        print("Some performance tests failed")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
