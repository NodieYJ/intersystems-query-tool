#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能基准测试模块

测试和监控关键性能指标
"""

import time
import unittest
import sys
import os
import json
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# 添加项目根目录
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.infrastructure.security.security_utils import SecurityUtils
from src.infrastructure.security.rate_limiter import RateLimiter, RateLimitConfig
from src.infrastructure.logging.security_audit import SecurityAuditLogger
from src.business.services.data_service import InputValidator


@dataclass
class BenchmarkResult:
  """基准测试结果"""
  name: str
  iterations: int
  total_time: float
  avg_time: float
  min_time: float
  max_time: float
  throughput: float  # operations per second
  timestamp: str


class PerformanceBenchmark:
  """性能基准测试类"""

  def __init__(self):
    self.results: List[BenchmarkResult] = []

  def run_benchmark(
    self,
    name: str,
    func,
    iterations: int = 1000,
    warmup: int = 10
  ) -> BenchmarkResult:
    """
    运行基准测试

    Args:
        name: 测试名称
        func: 测试函数
        iterations: 迭代次数
        warmup: 预热次数

    Returns:
        BenchmarkResult: 测试结果
    """
      # 预热
      for _ in range(warmup):
        func()
      
      # 计时测试
      times = []
      for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)
      
      # 计算统计
      total_time = sum(times)
      avg_time = total_time / iterations
      min_time = min(times)
      max_time = max(times)
      throughput = iterations / total_time if total_time > 0 else 0
      
      result = BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time=total_time,
        avg_time=avg_time,
        min_time=min_time,
        max_time=max_time,
        throughput=throughput,
        timestamp=datetime.now().isoformat()
      )
      
      self.results.append(result)
      return result

  def print_results(self) -> None:
    """打印测试结果"""
    print("\n" + "=" * 80)
    print("性能基准测试结果")
    print("=" * 80)
    
    for result in self.results:
      print(f"\n{result.name}:")
      print(f"  迭代次数: {result.iterations}")
      print(f"  总时间: {result.total_time:.4f}s")
      print(f"  平均时间: {result.avg_time * 1000:.4f}ms")
      print(f"  最小时间: {result.min_time * 1000:.4f}ms")
      print(f"  最大时间: {result.max_time * 1000:.4f}ms")
      print(f"  吞吐量: {result.throughput:.2f} ops/s")
    
    print("\n" + "=" * 80)

  def save_results(self, filepath: str = "benchmark_results.json") -> None:
    """保存测试结果到 JSON 文件"""
    results_dict = [asdict(r) for r in self.results]
    with open(filepath, 'w', encoding='utf-8') as f:
      json.dump(results_dict, f, indent=2, ensure_ascii=False)


class TestSecurityBenchmarks(unittest.TestCase):
  """安全功能性能基准测试"""

  def setUp(self):
    """设置测试环境"""
    self.benchmark = PerformanceBenchmark()

  def test_password_encryption_benchmark(self):
    """密码加密性能基准测试"""
    password = "Test@SecurePassword123!"
    
    result = self.benchmark.run_benchmark(
      name="密码加密",
      func=lambda: SecurityUtils.encrypt_password(password),
      iterations=100
    )
    
    # 加密应该在合理时间内（100次 < 2秒）
    self.assertLess(result.total_time, 2.0)
    # 吞吐量应该 > 50 ops/s
    self.assertGreater(result.throughput, 50)

  def test_password_verification_benchmark(self):
    """密码验证性能基准测试"""
    password = "Test@SecurePassword123!"
    encrypted = SecurityUtils.encrypt_password(password)
    
    result = self.benchmark.run_benchmark(
      name="密码验证",
      func=lambda: SecurityUtils.verify_password(password, encrypted),
      iterations=1000
    )
    
    # 验证应该在合理时间内（1000次 < 1秒）
    self.assertLess(result.total_time, 1.0)
    # 吞吐量应该 > 1000 ops/s
    self.assertGreater(result.throughput, 1000)

  def test_password_strength_check_benchmark(self):
    """密码强度检查性能基准测试"""
    password = "Test@SecurePassword123!"
    
    result = self.benchmark.run_benchmark(
      name="密码强度检查",
      func=lambda: SecurityUtils.check_password_strength(password),
      iterations=1000
    )
    
    # 强度检查应该在合理时间内（1000次 < 0.5秒）
    self.assertLess(result.total_time, 0.5)
    # 吞吐量应该 > 2000 ops/s
    self.assertGreater(result.throughput, 2000)

  def test_rate_limiter_benchmark(self):
    """速率限制器性能基准测试"""
    limiter = RateLimiter(RateLimitConfig(max_requests=1000))
    
    result = self.benchmark.run_benchmark(
      name="速率限制检查",
      func=lambda: limiter.check_rate_limit(f"client_{time.time_ns()}"),
      iterations=10000
    )
    
    # 10000次检查应该 < 1秒
    self.assertLess(result.total_time, 1.0)
    # 吞吐量应该 > 10000 ops/s
    self.assertGreater(result.throughput, 10000)

  def test_input_validation_benchmark(self):
    """输入验证性能基准测试"""
    query = "SELECT * FROM users WHERE id = ?"
    
    result = self.benchmark.run_benchmark(
      name="输入验证",
      func=lambda: InputValidator.validate_query_not_dangerous(query),
      iterations=5000
    )
    
    # 5000次验证应该 < 1秒
    self.assertLess(result.total_time, 1.0)
    # 吞吐量应该 > 5000 ops/s
    self.assertGreater(result.throughput, 5000)

  def test_schema_validation_benchmark(self):
    """Schema 验证性能基准测试"""
    schema = "public"
    
    result = self.benchmark.run_benchmark(
      name="Schema 验证",
      func=lambda: InputValidator.validate_schema_name(schema),
      iterations=5000
    )
    
    # 5000次验证应该 < 0.5秒
    self.assertLess(result.total_time, 0.5)
    # 吞吐量应该 > 10000 ops/s
    self.assertGreater(result.throughput, 10000)

  def test_constant_time_compare_benchmark(self):
    """恒定时间比较性能基准测试"""
    str1 = "a" * 100
    str2 = "a" * 100
    
    result = self.benchmark.run_benchmark(
      name="恒定时间比较",
      func=lambda: SecurityUtils._constant_time_compare(str1, str2),
      iterations=10000
    )
    
    # 10000次比较应该 < 0.1秒
    self.assertLess(result.total_time, 0.1)
    # 吞吐量应该 > 100000 ops/s
    self.assertGreater(result.throughput, 100000)

  def test_print_benchmarks(self):
    """打印所有基准测试结果"""
    password = "Test@SecurePassword123!"
    encrypted = SecurityUtils.encrypt_password(password)
    limiter = RateLimiter(RateLimitConfig(max_requests=1000))
    
    # 运行所有测试
    self.benchmark.run_benchmark("密码加密", lambda: SecurityUtils.encrypt_password(password), 100)
    self.benchmark.run_benchmark("密码验证", lambda: SecurityUtils.verify_password(password, encrypted), 1000)
    self.benchmark.run_benchmark("密码强度检查", lambda: SecurityUtils.check_password_strength(password), 1000)
    self.benchmark.run_benchmark("速率限制检查", lambda: limiter.check_rate_limit(f"client_{time.time_ns()}"), 10000)
    self.benchmark.run_benchmark("输入验证", lambda: InputValidator.validate_query_not_dangerous("SELECT * FROM users"), 5000)
    self.benchmark.run_benchmark("Schema 验证", lambda: InputValidator.validate_schema_name("public"), 5000)
    
    # 打印结果
    self.benchmark.print_results()
    
    # 保存结果
    self.benchmark.save_results("benchmark_results.json")


class TestPerformanceThresholds(unittest.TestCase):
  """性能阈值测试类"""

  def test_password_encryption_threshold(self):
    """密码加密阈值测试"""
    password = "Test@SecurePassword123!"
    
    # 单次加密应该 < 50ms
    start = time.perf_counter()
    SecurityUtils.encrypt_password(password)
    elapsed = time.perf_counter() - start
    
    self.assertLess(elapsed, 0.05, f"密码加密耗时 {elapsed * 1000:.2f}ms，超过 50ms 阈值")

  def test_password_verification_threshold(self):
    """密码验证阈值测试"""
    password = "Test@SecurePassword123!"
    encrypted = SecurityUtils.encrypt_password(password)
    
    # 单次验证应该 < 1ms
    start = time.perf_counter()
    SecurityUtils.verify_password(password, encrypted)
    elapsed = time.perf_counter() - start
    
    self.assertLess(elapsed, 0.001, f"密码验证耗时 {elapsed * 1000:.2f}ms，超过 1ms 阈值")

  def test_rate_limit_check_threshold(self):
    """速率限制检查阈值测试"""
    limiter = RateLimiter(RateLimitConfig(max_requests=1000))
    
    # 单次检查应该 < 0.1ms
    start = time.perf_counter()
    limiter.check_rate_limit("test_client")
    elapsed = time.perf_counter() - start
    
    self.assertLess(elapsed, 0.0001, f"速率限制检查耗时 {elapsed * 1000:.4f}ms，超过 0.1ms 阈值")


if __name__ == "__main__":
  unittest.main()
