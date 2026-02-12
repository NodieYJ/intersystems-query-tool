#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
监控面板系统

提供实时监控和可视化功能：
- 性能监控面板 (CPU、内存、吞吐量)
- 连接监控面板 (活跃连接、请求统计)
- 日志管理面板 (日志查看、筛选、导出)

支持HTTP API和WebSocket实时推送。
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    metric: str
    condition: str  # '>', '<', '>=', '<=', '==', '!='
    threshold: float
    duration: int  # 持续秒数
    enabled: bool = True
    severity: str = "warning"  # info, warning, error, critical
    description: str = ""


class MetricsCollector:
    """
    指标收集器
    
    收集和存储性能指标数据。
    """
    
    def __init__(
        self,
        max_history: int = 3600,  # 保存1小时的历史数据
        collection_interval: float = 5.0
    ):
        self._max_history = max_history
        self._collection_interval = collection_interval
        
        # 指标存储
        self._metrics: Dict[str, deque] = {}
        self._gauges: Dict[str, float] = {}
        self._counters: Dict[str, int] = {}
        
        # 收集任务
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
        
        # 回调
        self._on_metric: Optional[Callable[[str, MetricPoint], None]] = None
        
        logger.info(f"MetricsCollector initialized: interval={collection_interval}s")
    
    def set_metric_callback(self, callback: Callable[[str, MetricPoint], None]):
        """设置指标回调"""
        self._on_metric = callback
    
    async def start(self):
        """启动收集器"""
        if self._running:
            return
        
        self._running = True
        self._collection_task = asyncio.create_task(self._collect_loop())
        logger.info("MetricsCollector started")
    
    async def stop(self):
        """停止收集器"""
        self._running = False
        
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("MetricsCollector stopped")
    
    async def _collect_loop(self):
        """收集循环"""
        import psutil
        
        while self._running:
            try:
                # 收集系统指标
                await self._collect_system_metrics()
                
                # 触发回调
                if self._on_metric:
                    for name, history in self._metrics.items():
                        if history:
                            latest = history[-1]
                            self._on_metric(name, latest)
                
                await asyncio.sleep(self._collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"指标收集错误: {e}")
                await asyncio.sleep(self._collection_interval)
    
    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric("system_cpu_percent", cpu_percent)
            
            # 内存使用
            memory = psutil.virtual_memory()
            self.record_metric("system_memory_percent", memory.percent)
            self.record_metric("system_memory_used_mb", memory.used / 1024 / 1024)
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            self.record_metric("system_disk_percent", disk.percent)
            
        except ImportError:
            # psutil未安装，跳过系统指标
            pass
        except Exception as e:
            logger.warning(f"系统指标收集失败: {e}")
    
    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """记录指标"""
        if name not in self._metrics:
            self._metrics[name] = deque(maxlen=self._max_history)
        
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        
        self._metrics[name].append(point)
    
    def set_gauge(self, name: str, value: float):
        """设置仪表盘值"""
        self._gauges[name] = value
        self.record_metric(name, value)
    
    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        if name not in self._counters:
            self._counters[name] = 0
        
        self._counters[name] += value
        self.record_metric(name, self._counters[name])
    
    def get_metric_history(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取指标历史"""
        if name not in self._metrics:
            return []
        
        history = list(self._metrics[name])[-limit:]
        return [
            {
                'timestamp': p.timestamp,
                'value': p.value,
                'labels': p.labels
            }
            for p in history
        ]
    
    def get_latest_metric(self, name: str) -> Optional[Dict[str, Any]]:
        """获取最新指标值"""
        if name not in self._metrics or not self._metrics[name]:
            return None
        
        latest = self._metrics[name][-1]
        return {
            'timestamp': latest.timestamp,
            'value': latest.value,
            'labels': latest.labels
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        result = {
            'gauges': self._gauges.copy(),
            'counters': self._counters.copy(),
            'latest': {}
        }
        
        for name, history in self._metrics.items():
            if history:
                latest = history[-1]
                result['latest'][name] = {
                    'value': latest.value,
                    'timestamp': latest.timestamp
                }
        
        return result


class PerformanceDashboard:
    """
    性能监控面板
    
    监控服务器性能指标：
    - CPU使用率
    - 内存使用
    - 吞吐量
    - 响应时间
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self._metrics = metrics_collector
        
        # 性能统计
        self._request_times: deque = deque(maxlen=1000)
        self._error_count = 0
        self._total_requests = 0
        
        logger.info("PerformanceDashboard initialized")
    
    def record_request(self, duration: float, success: bool = True):
        """记录请求"""
        self._request_times.append(duration)
        self._total_requests += 1
        
        if not success:
            self._error_count += 1
        
        # 更新指标
        self._metrics.increment_counter("http_requests_total")
        if not success:
            self._metrics.increment_counter("http_errors_total")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self._request_times:
            return {
                'total_requests': 0,
                'error_count': 0,
                'error_rate': 0.0,
                'avg_response_time': 0.0,
                'p50_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0
            }
        
        times = sorted(self._request_times)
        n = len(times)
        
        return {
            'total_requests': self._total_requests,
            'error_count': self._error_count,
            'error_rate': self._error_count / self._total_requests if self._total_requests > 0 else 0.0,
            'avg_response_time': sum(times) / n,
            'p50_response_time': times[int(n * 0.5)],
            'p95_response_time': times[int(n * 0.95)] if n > 20 else times[-1],
            'p99_response_time': times[int(n * 0.99)] if n > 100 else times[-1],
            'min_response_time': times[0],
            'max_response_time': times[-1]
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取面板数据"""
        # 系统指标
        system_metrics = {
            'cpu': self._metrics.get_latest_metric('system_cpu_percent'),
            'memory': self._metrics.get_latest_metric('system_memory_percent'),
            'disk': self._metrics.get_latest_metric('system_disk_percent')
        }
        
        # 性能指标
        performance = self.get_performance_stats()
        
        # 历史数据 (最近60个点)
        cpu_history = self._metrics.get_metric_history('system_cpu_percent', 60)
        memory_history = self._metrics.get_metric_history('system_memory_percent', 60)
        
        return {
            'timestamp': time.time(),
            'system': system_metrics,
            'performance': performance,
            'history': {
                'cpu': cpu_history,
                'memory': memory_history
            }
        }


class ConnectionDashboard:
    """
    连接监控面板
    
    监控连接状态和请求统计。
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self._metrics = metrics_collector
        
        # 连接统计
        self._active_connections: Set[str] = set()
        self._connection_history: deque = deque(maxlen=1000)
        
        # 请求统计
        self._requests_by_endpoint: Dict[str, int] = {}
        
        logger.info("ConnectionDashboard initialized")
    
    def add_connection(self, connection_id: str, info: Dict[str, Any]):
        """添加连接"""
        self._active_connections.add(connection_id)
        self._connection_history.append({
            'event': 'connect',
            'connection_id': connection_id,
            'timestamp': time.time(),
            'info': info
        })
        
        self._metrics.set_gauge('active_connections', len(self._active_connections))
        self._metrics.increment_counter('total_connections')
    
    def remove_connection(self, connection_id: str):
        """移除连接"""
        self._active_connections.discard(connection_id)
        self._connection_history.append({
            'event': 'disconnect',
            'connection_id': connection_id,
            'timestamp': time.time()
        })
        
        self._metrics.set_gauge('active_connections', len(self._active_connections))
    
    def record_request(self, endpoint: str, method: str = "GET"):
        """记录请求"""
        key = f"{method}:{endpoint}"
        if key not in self._requests_by_endpoint:
            self._requests_by_endpoint[key] = 0
        self._requests_by_endpoint[key] += 1
        
        self._metrics.increment_counter(f'requests_{method}_{endpoint.replace("/", "_")}')
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        return {
            'active_connections': len(self._active_connections),
            'total_connections': self._metrics._counters.get('total_connections', 0),
            'connection_ids': list(self._active_connections)[:100]  # 最多100个
        }
    
    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        return {
            'requests_by_endpoint': self._requests_by_endpoint,
            'total_requests': sum(self._requests_by_endpoint.values())
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取面板数据"""
        return {
            'timestamp': time.time(),
            'connections': self.get_connection_stats(),
            'requests': self.get_request_stats(),
            'history': list(self._connection_history)[-100:]  # 最近100个事件
        }


class LogManager:
    """
    日志管理器
    
    管理和查询日志数据。
    """
    
    def __init__(
        self,
        max_entries: int = 10000,
        buffer_size: int = 1000
    ):
        self._max_entries = max_entries
        self._buffer_size = buffer_size
        
        # 日志存储
        self._logs: deque = deque(maxlen=max_entries)
        self._buffer: List[Dict[str, Any]] = []
        
        # 统计
        self._log_counts: Dict[str, int] = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        }
        
        logger.info("LogManager initialized")
    
    def add_log(
        self,
        level: str,
        message: str,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """添加日志条目"""
        entry = {
            'timestamp': time.time(),
            'level': level.upper(),
            'message': message,
            'source': source,
            'metadata': metadata or {}
        }
        
        self._buffer.append(entry)
        
        # 更新统计
        if level.upper() in self._log_counts:
            self._log_counts[level.upper()] += 1
        
        # 批量写入
        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer()
    
    def _flush_buffer(self):
        """刷新缓冲区"""
        for entry in self._buffer:
            self._logs.append(entry)
        self._buffer.clear()
    
    def query_logs(
        self,
        level: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """查询日志"""
        self._flush_buffer()
        
        results = []
        
        for entry in self._logs:
            # 级别筛选
            if level and entry['level'] != level.upper():
                continue
            
            # 来源筛选
            if source and source not in entry.get('source', ''):
                continue
            
            # 时间范围筛选
            if start_time and entry['timestamp'] < start_time:
                continue
            if end_time and entry['timestamp'] > end_time:
                continue
            
            # 内容搜索
            if search and search.lower() not in entry['message'].lower():
                continue
            
            results.append(entry)
        
        # 分页
        return results[offset:offset + limit]
    
    def get_log_stats(self) -> Dict[str, Any]:
        """获取日志统计"""
        self._flush_buffer()
        
        return {
            'total_entries': len(self._logs) + len(self._buffer),
            'counts': self._log_counts.copy(),
            'buffer_size': len(self._buffer)
        }
    
    def export_logs(
        self,
        format: str = "json",
        level: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """导出日志"""
        logs = self.query_logs(
            level=level,
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        if format == "json":
            return json.dumps(logs, indent=2, ensure_ascii=False)
        elif format == "csv":
            lines = ["timestamp,level,source,message"]
            for log in logs:
                lines.append(f"{log['timestamp']},{log['level']},{log.get('source', '')},\"{log['message']}\"")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def clear_logs(self):
        """清空日志"""
        self._logs.clear()
        self._buffer.clear()
        for key in self._log_counts:
            self._log_counts[key] = 0
        
        logger.info("Logs cleared")


class MonitoringSystem:
    """
    监控系统
    
    整合所有监控功能。
    """
    
    def __init__(self):
        # 组件
        self._metrics = MetricsCollector()
        self._performance = PerformanceDashboard(self._metrics)
        self._connections = ConnectionDashboard(self._metrics)
        self._logs = LogManager()
        
        # 告警规则
        self._alert_rules: Dict[str, AlertRule] = {}
        self._alert_history: deque = deque(maxlen=1000)
        
        logger.info("MonitoringSystem initialized")
    
    async def start(self):
        """启动监控系统"""
        await self._metrics.start()
        logger.info("MonitoringSystem started")
    
    async def stop(self):
        """停止监控系统"""
        await self._metrics.stop()
        logger.info("MonitoringSystem stopped")
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self._alert_rules[rule.rule_id] = rule
        logger.info(f"Alert rule added: {rule.name}")
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警"""
        alerts = []
        
        for rule in self._alert_rules.values():
            if not rule.enabled:
                continue
            
            # 获取指标值
            metric = self._metrics.get_latest_metric(rule.metric)
            if not metric:
                continue
            
            value = metric['value']
            
            # 检查条件
            triggered = False
            if rule.condition == '>' and value > rule.threshold:
                triggered = True
            elif rule.condition == '<' and value < rule.threshold:
                triggered = True
            elif rule.condition == '>=' and value >= rule.threshold:
                triggered = True
            elif rule.condition == '<=' and value <= rule.threshold:
                triggered = True
            elif rule.condition == '==' and value == rule.threshold:
                triggered = True
            elif rule.condition == '!=' and value != rule.threshold:
                triggered = True
            
            if triggered:
                alert = {
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'severity': rule.severity,
                    'metric': rule.metric,
                    'value': value,
                    'threshold': rule.threshold,
                    'condition': rule.condition,
                    'timestamp': time.time(),
                    'description': rule.description
                }
                alerts.append(alert)
                self._alert_history.append(alert)
        
        return alerts
    
    def get_overview(self) -> Dict[str, Any]:
        """获取监控概览"""
        return {
            'timestamp': time.time(),
            'performance': self._performance.get_performance_stats(),
            'connections': self._connections.get_connection_stats(),
            'logs': self._logs.get_log_stats(),
            'system': self._metrics.get_all_metrics()['latest'],
            'alerts': self.check_alerts()[:10]  # 最近10个告警
        }
    
    def get_performance_dashboard(self) -> Dict[str, Any]:
        """获取性能面板"""
        return self._performance.get_dashboard_data()
    
    def get_connection_dashboard(self) -> Dict[str, Any]:
        """获取连接面板"""
        return self._connections.get_dashboard_data()
    
    def get_logs(
        self,
        level: Optional[str] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """获取日志"""
        return self._logs.query_logs(level=level, limit=limit, **kwargs)
    
    # 代理方法
    def record_request(self, duration: float, success: bool = True):
        """记录请求"""
        self._performance.record_request(duration, success)
    
    def add_connection(self, connection_id: str, info: Dict[str, Any]):
        """添加连接"""
        self._connections.add_connection(connection_id, info)
    
    def remove_connection(self, connection_id: str):
        """移除连接"""
        self._connections.remove_connection(connection_id)
    
    def record_endpoint_request(self, endpoint: str, method: str = "GET"):
        """记录端点请求"""
        self._connections.record_request(endpoint, method)
    
    def add_log(self, level: str, message: str, **kwargs):
        """添加日志"""
        self._logs.add_log(level, message, **kwargs)


def create_monitoring_system() -> MonitoringSystem:
    """创建监控系统"""
    return MonitoringSystem()
