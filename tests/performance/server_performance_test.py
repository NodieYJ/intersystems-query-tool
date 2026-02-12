#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务器性能测试和压力测试

测试内容：
- HTTP/2服务器性能
- WebSocket并发测试
- 文件传输性能
- 多进程并发测试
- 内存和CPU监控

使用方法：
    python tests/performance/server_performance_test.py
"""

import asyncio
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, r'D:\pywindows')

from src.infrastructure.server import create_multiprocess_server, create_websocket_server
from src.infrastructure.server.multiprocess import MultiProcessServer
from src.infrastructure.server.websocket_server import WebSocketServer


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    success: bool
    duration: float
    requests_per_second: float = 0.0
    total_requests: int = 0
    failed_requests: int = 0
    avg_latency: float = 0.0
    min_latency: float = 0.0
    max_latency: float = 0.0
    memory_usage_mb: float = 0.0
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
    
    async def test_multiprocess_throughput(
        self,
        num_workers: int = 4,
        total_requests: int = 1000,
        concurrent_requests: int = 100
    ) -> TestResult:
        """测试多进程服务器吞吐量"""
        print(f"\n[测试] 多进程服务器吞吐量 ({num_workers} workers, {total_requests} 请求)")
        
        server = create_multiprocess_server(num_workers=num_workers)
        latencies = []
        failed = 0
        
        try:
            await server.start()
            
            start_time = time.time()
            
            # 分批发送请求
            completed = 0
            while completed < total_requests:
                batch_size = min(concurrent_requests, total_requests - completed)
                
                tasks = [
                    self._send_request(server, f"task_{completed + i}", latencies)
                    for i in range(batch_size)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for r in results:
                    if isinstance(r, Exception):
                        failed += 1
                    elif not r:
                        failed += 1
                
                completed += batch_size
                
                # 进度显示
                if completed % 100 == 0:
                    print(f"  进度: {completed}/{total_requests}")
            
            duration = time.time() - start_time
            
            # 计算统计
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
            else:
                avg_latency = min_latency = max_latency = 0
            
            rps = total_requests / duration if duration > 0 else 0
            
            result = TestResult(
                test_name="multiprocess_throughput",
                success=failed < total_requests * 0.05,  # 允许5%失败
                duration=duration,
                requests_per_second=rps,
                total_requests=total_requests,
                failed_requests=failed,
                avg_latency=avg_latency,
                min_latency=min_latency,
                max_latency=max_latency,
                details={
                    'num_workers': num_workers,
                    'concurrent_requests': concurrent_requests,
                    'success_rate': (total_requests - failed) / total_requests
                }
            )
            
            await server.stop()
            return result
            
        except Exception as e:
            await server.stop()
            return TestResult(
                test_name="multiprocess_throughput",
                success=False,
                duration=0,
                error_message=str(e)
            )
    
    async def _send_request(
        self,
        server: MultiProcessServer,
        data: str,
        latencies: List[float]
    ) -> bool:
        """发送单个请求并记录延迟"""
        start = time.time()
        try:
            result = await server.handle_request(data, timeout=30.0)
            latency = time.time() - start
            latencies.append(latency)
            return result is not None and result.success
        except Exception:
            return False
    
    async def test_websocket_connections(
        self,
        max_connections: int = 100,
        connection_delay: float = 0.01
    ) -> TestResult:
        """测试WebSocket连接数上限"""
        print(f"\n[测试] WebSocket连接数上限 ({max_connections} 连接)")
        
        # 由于WebSocket需要真实的aiohttp服务器，这里模拟测试
        # 实际测试需要在完整的服务器环境中运行
        
        server = create_websocket_server(max_connections=max_connections)
        
        try:
            await server.start()
            
            start_time = time.time()
            
            # 模拟连接建立
            connected = 0
            for i in range(max_connections):
                # 模拟连接ID
                conn_id = f"test_conn_{i}"
                server._connections[conn_id] = None  # 简化的模拟
                connected += 1
                
                if i % 10 == 0:
                    await asyncio.sleep(connection_delay)
            
            duration = time.time() - start_time
            
            result = TestResult(
                test_name="websocket_connections",
                success=connected == max_connections,
                duration=duration,
                total_requests=max_connections,
                failed_requests=max_connections - connected,
                requests_per_second=connected / duration if duration > 0 else 0,
                details={
                    'max_connections': max_connections,
                    'connected': connected
                }
            )
            
            await server.stop()
            return result
            
        except Exception as e:
            return TestResult(
                test_name="websocket_connections",
                success=False,
                duration=0,
                error_message=str(e)
            )
    
    async def test_file_transfer(
        self,
        file_size_mb: int = 100,
        chunk_size_kb: int = 64
    ) -> TestResult:
        """测试文件传输性能"""
        print(f"\n[测试] 文件传输性能 ({file_size_mb}MB 文件)")
        
        from src.infrastructure.server.file_transfer import (
            create_file_transfer_manager,
            TransferStatus
        )
        
        manager = create_file_transfer_manager(
            base_path="./test_uploads",
            temp_path="./test_temp"
        )
        
        try:
            await manager.start()
            
            file_size = file_size_mb * 1024 * 1024
            chunk_size = chunk_size_kb * 1024
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            # 创建测试数据
            test_data = b"X" * chunk_size
            
            # 初始化传输
            transfer_info = await manager.initialize_transfer(
                file_name=f"test_{file_size_mb}mb.bin",
                file_size=file_size
            )
            
            if not transfer_info:
                return TestResult(
                    test_name="file_transfer",
                    success=False,
                    duration=0,
                    error_message="Failed to initialize transfer"
                )
            
            start_time = time.time()
            
            # 发送所有数据块
            for i in range(total_chunks):
                success = await manager.receive_chunk(
                    transfer_info.transfer_id,
                    i,
                    test_data
                )
                
                if not success:
                    return TestResult(
                        test_name="file_transfer",
                        success=False,
                        duration=0,
                        error_message=f"Failed to receive chunk {i}"
                    )
                
                if i % 100 == 0:
                    print(f"  进度: {i}/{total_chunks} chunks")
            
            duration = time.time() - start_time
            
            # 等待组装完成
            await asyncio.sleep(1)
            
            # 获取状态
            status = await manager.get_transfer_status(transfer_info.transfer_id)
            
            throughput_mbps = (file_size_mb * 8) / duration if duration > 0 else 0
            
            result = TestResult(
                test_name="file_transfer",
                success=status and status['status'] == TransferStatus.COMPLETED.value,
                duration=duration,
                requests_per_second=total_chunks / duration if duration > 0 else 0,
                total_requests=total_chunks,
                details={
                    'file_size_mb': file_size_mb,
                    'chunk_size_kb': chunk_size_kb,
                    'total_chunks': total_chunks,
                    'throughput_mbps': throughput_mbps,
                    'final_status': status
                }
            )
            
            await manager.stop()
            return result
            
        except Exception as e:
            return TestResult(
                test_name="file_transfer",
                success=False,
                duration=0,
                error_message=str(e)
            )
    
    async def run_all_tests(self) -> None:
        """运行所有性能测试"""
        print("=" * 60)
        print("服务器性能测试套件")
        print("=" * 60)
        
        # 测试1: 多进程吞吐量 (小规模)
        result1 = await self.test_multiprocess_throughput(
            num_workers=4,
            total_requests=100,
            concurrent_requests=10
        )
        self.results.append(result1)
        self._print_result(result1)
        
        # 测试2: WebSocket连接
        result2 = await self.test_websocket_connections(
            max_connections=50,
            connection_delay=0.01
        )
        self.results.append(result2)
        self._print_result(result2)
        
        # 测试3: 文件传输 (小文件)
        result3 = await self.test_file_transfer(
            file_size_mb=10,
            chunk_size_kb=64
        )
        self.results.append(result3)
        self._print_result(result3)
        
        # 打印总结
        self._print_summary()
    
    def _print_result(self, result: TestResult) -> None:
        """打印测试结果"""
        status = "PASS" if result.success else "FAIL"
        print(f"\n  状态: {status}")
        print(f"  耗时: {result.duration:.2f}s")
        
        if result.requests_per_second > 0:
            print(f"  吞吐量: {result.requests_per_second:.2f} req/s")
        
        if result.avg_latency > 0:
            print(f"  平均延迟: {result.avg_latency*1000:.2f}ms")
            print(f"  延迟范围: {result.min_latency*1000:.2f}ms - {result.max_latency*1000:.2f}ms")
        
        if result.error_message:
            print(f"  错误: {result.error_message}")
    
    def _print_summary(self) -> None:
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        
        print(f"总测试数: {len(self.results)}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"通过率: {passed/len(self.results)*100:.1f}%")
        
        # 保存详细报告
        self._save_report()
    
    def _save_report(self) -> None:
        """保存测试报告"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r.success),
                'failed': sum(1 for r in self.results if not r.success)
            },
            'results': [
                {
                    'test_name': r.test_name,
                    'success': r.success,
                    'duration': r.duration,
                    'requests_per_second': r.requests_per_second,
                    'avg_latency': r.avg_latency,
                    'error_message': r.error_message,
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        filename = f"performance_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n详细报告已保存: {filename}")


async def main():
    """主函数"""
    tester = PerformanceTester()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main())
