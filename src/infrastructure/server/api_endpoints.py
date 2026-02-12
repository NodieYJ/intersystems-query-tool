#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务器管理API端点

提供HTTP API接口用于：
- 健康检查 (/health)
- 状态查询 (/status, /stats)
- 监控数据 (/metrics, /monitoring/*)
- 管理操作 (/admin/*)

所有端点返回JSON格式数据。
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class APIEndpoint:
    """API端点基类"""
    
    def __init__(self, path: str, method: str = "GET"):
        self.path = path
        self.method = method.upper()
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        raise NotImplementedError


class HealthEndpoint(APIEndpoint):
    """
    健康检查端点
    
    GET /health
    
    返回服务器健康状态。
    """
    
    def __init__(self, get_health_fn: Optional[Callable[[], Dict[str, Any]]] = None):
        super().__init__("/health", "GET")
        self._get_health = get_health_fn
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理健康检查请求"""
        health = {
            'status': 'healthy',
            'timestamp': time.time(),
            'uptime': time.time() - getattr(self, '_start_time', time.time()),
            'version': '1.0.0'
        }
        
        if self._get_health:
            custom_health = self._get_health()
            health.update(custom_health)
        
        return health


class StatusEndpoint(APIEndpoint):
    """
    状态查询端点
    
    GET /status
    
    返回服务器详细状态。
    """
    
    def __init__(self, get_status_fn: Optional[Callable[[], Dict[str, Any]]] = None):
        super().__init__("/status", "GET")
        self._get_status = get_status_fn
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态查询请求"""
        if self._get_status:
            return self._get_status()
        
        return {
            'status': 'running',
            'timestamp': time.time()
        }


class MetricsEndpoint(APIEndpoint):
    """
    指标端点
    
    GET /metrics
    
    返回Prometheus格式的指标数据（可选）。
    """
    
    def __init__(self, get_metrics_fn: Optional[Callable[[], Dict[str, Any]]] = None):
        super().__init__("/metrics", "GET")
        self._get_metrics = get_metrics_fn
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理指标请求"""
        if self._get_metrics:
            metrics = self._get_metrics()
            
            # 检查是否请求Prometheus格式
            if request.get('headers', {}).get('Accept') == 'text/plain':
                return {
                    'content_type': 'text/plain',
                    'body': self._format_prometheus(metrics)
                }
            
            return metrics
        
        return {'metrics': {}}
    
    def _format_prometheus(self, metrics: Dict[str, Any]) -> str:
        """格式化为Prometheus格式"""
        lines = []
        
        for name, data in metrics.items():
            if isinstance(data, dict):
                value = data.get('value', 0)
                labels = data.get('labels', {})
                
                label_str = ','.join([f'{k}="{v}"' for k, v in labels.items()])
                if label_str:
                    lines.append(f'{name}{{{label_str}}} {value}')
                else:
                    lines.append(f'{name} {value}')
        
        return '\n'.join(lines)


class MonitoringOverviewEndpoint(APIEndpoint):
    """
    监控概览端点
    
    GET /monitoring/overview
    
    返回监控概览数据。
    """
    
    def __init__(self, monitoring_system=None):
        super().__init__("/monitoring/overview", "GET")
        self._monitoring = monitoring_system
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理监控概览请求"""
        if self._monitoring:
            return self._monitoring.get_overview()
        
        return {'error': 'Monitoring system not available'}


class MonitoringPerformanceEndpoint(APIEndpoint):
    """
    性能监控端点
    
    GET /monitoring/performance
    
    返回性能监控数据。
    """
    
    def __init__(self, monitoring_system=None):
        super().__init__("/monitoring/performance", "GET")
        self._monitoring = monitoring_system
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理性能监控请求"""
        if self._monitoring:
            return self._monitoring.get_performance_dashboard()
        
        return {'error': 'Monitoring system not available'}


class MonitoringConnectionsEndpoint(APIEndpoint):
    """
    连接监控端点
    
    GET /monitoring/connections
    
    返回连接监控数据。
    """
    
    def __init__(self, monitoring_system=None):
        super().__init__("/monitoring/connections", "GET")
        self._monitoring = monitoring_system
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理连接监控请求"""
        if self._monitoring:
            return self._monitoring.get_connection_dashboard()
        
        return {'error': 'Monitoring system not available'}


class LogsQueryEndpoint(APIEndpoint):
    """
    日志查询端点
    
    GET /monitoring/logs
    
    查询日志数据。
    
    Query参数:
        - level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - limit: 返回条目数 (默认100)
        - offset: 偏移量
        - search: 搜索关键词
    """
    
    def __init__(self, monitoring_system=None):
        super().__init__("/monitoring/logs", "GET")
        self._monitoring = monitoring_system
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理日志查询请求"""
        if not self._monitoring:
            return {'error': 'Monitoring system not available'}
        
        query_params = request.get('query', {})
        
        level = query_params.get('level')
        limit = int(query_params.get('limit', 100))
        offset = int(query_params.get('offset', 0))
        search = query_params.get('search')
        
        logs = self._monitoring.get_logs(
            level=level,
            limit=limit,
            offset=offset,
            search=search
        )
        
        return {
            'logs': logs,
            'total': len(logs),  # 实际应该返回总数
            'limit': limit,
            'offset': offset
        }


class AdminStatsEndpoint(APIEndpoint):
    """
    管理统计端点
    
    GET /admin/stats
    
    返回服务器统计信息（管理员）。
    """
    
    def __init__(self, get_stats_fn: Optional[Callable[[], Dict[str, Any]]] = None):
        super().__init__("/admin/stats", "GET")
        self._get_stats = get_stats_fn
    
    async def handle(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理统计请求"""
        if self._get_stats:
            return self._get_stats()
        
        return {'stats': {}}


class APIRouter:
    """
    API路由器
    
    管理所有API端点。
    """
    
    def __init__(self):
        self._endpoints: Dict[str, APIEndpoint] = {}
    
    def register(self, endpoint: APIEndpoint):
        """注册端点"""
        key = f"{endpoint.method}:{endpoint.path}"
        self._endpoints[key] = endpoint
        logger.info(f"API endpoint registered: {endpoint.method} {endpoint.path}")
    
    async def route(self, path: str, method: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """路由请求到对应端点"""
        key = f"{method.upper()}:{path}"
        
        endpoint = self._endpoints.get(key)
        if not endpoint:
            return None
        
        try:
            return await endpoint.handle(request)
        except Exception as e:
            logger.error(f"API endpoint error: {path} - {e}")
            return {
                'error': 'Internal server error',
                'message': str(e)
            }
    
    def get_routes(self) -> List[Dict[str, str]]:
        """获取所有路由"""
        return [
            {'method': ep.method, 'path': ep.path}
            for ep in self._endpoints.values()
        ]


def create_default_api_router(
    monitoring_system=None,
    get_health_fn=None,
    get_status_fn=None,
    get_stats_fn=None
) -> APIRouter:
    """
    创建默认API路由器
    
    注册所有默认端点。
    """
    router = APIRouter()
    
    # 健康检查
    router.register(HealthEndpoint(get_health_fn))
    
    # 状态查询
    router.register(StatusEndpoint(get_status_fn))
    
    # 指标
    router.register(MetricsEndpoint())
    
    # 监控
    if monitoring_system:
        router.register(MonitoringOverviewEndpoint(monitoring_system))
        router.register(MonitoringPerformanceEndpoint(monitoring_system))
        router.register(MonitoringConnectionsEndpoint(monitoring_system))
        router.register(LogsQueryEndpoint(monitoring_system))
    
    # 管理
    router.register(AdminStatsEndpoint(get_stats_fn))
    
    return router


# 端点文档
API_ENDPOINTS_DOC = """
# QueryTool Server API Documentation

## Base URL
```
http://localhost:8080
```

## Endpoints

### Health Check
```
GET /health
```

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1707734400.0,
  "uptime": 3600,
  "version": "1.0.0"
}
```

### Server Status
```
GET /status
```

Returns detailed server status.

**Response:**
```json
{
  "status": "running",
  "timestamp": 1707734400.0,
  "active_connections": 42,
  "total_requests": 15000
}
```

### Metrics
```
GET /metrics
```

Returns server metrics.

**Response:**
```json
{
  "system_cpu_percent": {"value": 15.5, "timestamp": 1707734400.0},
  "system_memory_percent": {"value": 45.2, "timestamp": 1707734400.0}
}
```

### Monitoring Overview
```
GET /monitoring/overview
```

Returns monitoring overview data.

**Response:**
```json
{
  "timestamp": 1707734400.0,
  "performance": {...},
  "connections": {...},
  "logs": {...},
  "alerts": [...]
}
```

### Performance Dashboard
```
GET /monitoring/performance
```

Returns performance monitoring data.

**Response:**
```json
{
  "timestamp": 1707734400.0,
  "system": {
    "cpu": {"value": 15.5, "timestamp": 1707734400.0},
    "memory": {"value": 45.2, "timestamp": 1707734400.0}
  },
  "performance": {
    "total_requests": 1000,
    "error_rate": 0.01,
    "avg_response_time": 0.05,
    "p95_response_time": 0.1
  }
}
```

### Connections Dashboard
```
GET /monitoring/connections
```

Returns connection monitoring data.

**Response:**
```json
{
  "timestamp": 1707734400.0,
  "connections": {
    "active_connections": 42,
    "total_connections": 150
  },
  "requests": {...}
}
```

### Query Logs
```
GET /monitoring/logs?level=ERROR&limit=50
```

Query log entries.

**Query Parameters:**
- `level`: Log level filter (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `limit`: Maximum number of entries (default: 100)
- `offset`: Offset for pagination (default: 0)
- `search`: Search keyword

**Response:**
```json
{
  "logs": [
    {
      "timestamp": 1707734400.0,
      "level": "ERROR",
      "message": "Connection failed",
      "source": "server"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Admin Stats
```
GET /admin/stats
```

Returns detailed server statistics (admin only).

**Response:**
```json
{
  "stats": {
    "workers": {...},
    "memory": {...},
    "disk": {...}
  }
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Error description"
}
```

**Common HTTP Status Codes:**
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error
"""
