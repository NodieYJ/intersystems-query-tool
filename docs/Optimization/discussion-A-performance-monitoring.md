# 深入讨论：性能监控

**讨论时间**：2026年2月11日 19:40:00  
**参与人员**：AI Assistant + 用户

---

## 6.5.1 当前性能监控现状

### 已有的性能监控功能

| 功能 | 实现位置 | 状态 | 质量 |
|------|---------|------|------|
| **FPS监视器** | `performance.py` | ✅ 完整 | ⭐⭐⭐⭐ |
| **内存管理器** | `performance.py` | ✅ 完整 | ⭐⭐⭐ |
| **事件压缩器** | `performance.py` | ✅ 完整 | ⭐⭐⭐⭐ |
| **延迟更新器** | `performance.py` | ✅ 完整 | ⭐⭐⭐⭐ |
| **查询时间记录** | `sql_query_dialog.py` | ✅ 部分 | ⭐⭐⭐ |

### 现有架构

```python
# 现有 PerformanceOptimizer
class PerformanceOptimizer:
    def __init__(self):
        self.fps_monitor = FPSMonitor()
        self.memory_manager = MemoryManager()
        self.event_compressors = {}
        self.deferred_updaters = {}
    
    def get_performance_stats(self) -> Dict:
        return {
            "fps": self.fps_monitor.get_fps(),
            "memory": self.memory_manager.get_stats(),
            "event_compressors": list(self.event_compressors.keys())
        }
```

---

## 6.5.2 性能监控问题分析

### 缺失的功能

| # | 缺失功能 | 影响 | 严重程度 |
|---|---------|------|----------|
| **1** | 数据库查询监控 | 无法追踪慢查询 | 🟡 中 |
| **2** | API调用统计 | 无法分析调用频率 | 🟡 中 |
| **3** | 性能告警 | 问题难以及时发现 | 🟡 中 |
| **4** | 可视化面板 | 难以直观查看 | 🟡 低 |
| **5** | 性能基准测试 | 难以发现性能退化 | 🟡 低 |

### 现有功能的问题

| # | 问题 | 描述 | 严重程度 |
|---|------|------|----------|
| **1** | 统计数据未持久化 | 重启后数据丢失 | 🟡 低 |
| **2** | 缺少自动分析 | 需要人工查看 | 🟡 中 |
| **3** | 阈值未配置 | 无法设置告警阈值 | 🟡 低 |

---

## 6.5.3 性能监控增强方案

### 方案1：查询性能监控

```python
# src/infrastructure/monitoring/query_monitor.py

import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """查询指标"""
    query: str
    execution_time: float
    timestamp: float
    status: str  # success/failed
    row_count: int = 0

class QueryMonitor:
    """查询性能监控器"""
    
    def __init__(self, max_queries: int = 1000):
        self.max_queries = max_queries
        self.queries: List[QueryMetrics] = []
        self.query_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'failed_count': 0
        })
    
    def record_query(
        self,
        query: str,
        execution_time: float,
        status: str,
        row_count: int = 0
    ):
        """记录查询"""
        metrics = QueryMetrics(
            query=query,
            execution_time=execution_time,
            timestamp=time.time(),
            status=status,
            row_count=row_count
        )
        
        self.queries.append(metrics)
        
        # 保持最大数量
        if len(self.queries) > self.max_queries:
            self.queries = self.queries[-self.max_queries:]
        
        # 更新统计
        stats = self.query_stats[query[:100]]  # 只取前100字符作为key
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        
        if status == 'failed':
            stats['failed_count'] += 1
        
        # 检查慢查询
        if execution_time > 5.0:  # 超过5秒
            logger.warning(f"慢查询 ({execution_time:.2f}s): {query[:100]}")
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[QueryMetrics]:
        """获取慢查询"""
        return [q for q in self.queries if q.execution_time > threshold]
    
    def get_query_stats(self, query: str = None) -> Dict:
        """获取查询统计"""
        if query:
            return self.query_stats.get(query[:100], {})
        return dict(self.query_stats)
    
    def get_performance_report(self) -> Dict:
        """生成性能报告"""
        successful_queries = [q for q in self.queries if q.status == 'success']
        failed_queries = [q for q in self.queries if q.status == 'failed']
        
        if not successful_queries:
            return {'message': '没有查询数据'}
        
        execution_times = [q.execution_time for q in successful_queries]
        
        return {
            'total_queries': len(self.queries),
            'successful_queries': len(successful_queries),
            'failed_queries': len(failed_queries),
            'success_rate': len(successful_queries) / len(self.queries) * 100,
            'avg_execution_time': sum(execution_times) / len(execution_times),
            'min_execution_time': min(execution_times),
            'max_execution_time': max(execution_times),
            'slow_query_count': len(self.get_slow_queries(threshold=1.0))
        }
```

### 方案2：性能告警系统

```python
# src/infrastructure/monitoring/alert_manager.py

import logging
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str  # fps, memory, query_time, etc.
    condition: str  # lt, gt, eq, etc.
    threshold: float
    level: AlertLevel
    enabled: bool = True

class AlertManager:
    """性能告警管理器"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alerts: List[Dict] = []
        self.callbacks: List[Callable] = []
        
        # 默认告警规则
        self._add_default_rules()
    
    def _add_default_rules(self):
        """添加默认规则"""
        self.rules.extend([
            AlertRule(
                name="低FPS告警",
                metric="fps",
                condition="lt",
                threshold=30,
                level=AlertLevel.WARNING
            ),
            AlertRule(
                name="高内存使用",
                metric="memory_mb",
                condition="gt",
                threshold=512,
                level=AlertLevel.WARNING
            ),
            AlertRule(
                name="慢查询告警",
                metric="query_time",
                condition="gt",
                threshold=5.0,
                level=AlertLevel.WARNING
            ),
            AlertRule(
                name="高内存使用（严重）",
                metric="memory_mb",
                condition="gt",
                threshold=1024,
                level=AlertLevel.CRITICAL
            )
        ])
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
    
    def remove_rule(self, name: str):
        """移除告警规则"""
        self.rules = [r for r in self.rules if r.name != name]
    
    def check_metric(self, metric: str, value: float):
        """检查指标"""
        for rule in self.rules:
            if rule.metric != metric or not rule.enabled:
                continue
            
            triggered = False
            if rule.condition == "lt" and value < rule.threshold:
                triggered = True
            elif rule.condition == "gt" and value > rule.threshold:
                triggered = True
            elif rule.condition == "eq" and value == rule.threshold:
                triggered = True
            
            if triggered:
                self._trigger_alert(rule, value)
    
    def _trigger_alert(self, rule: AlertRule, value: float):
        """触发告警"""
        alert = {
            'rule_name': rule.name,
            'level': rule.level.value,
            'metric': rule.metric,
            'value': value,
            'threshold': rule.threshold,
            'timestamp': datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        
        # 记录日志
        logger.warning(f"性能告警 [{rule.level.value}]: {rule.name} - {metric}={value}")
        
        # 调用回调
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    def add_callback(self, callback: Callable):
        """添加告警回调"""
        self.callbacks.append(callback)
    
    def get_alerts(self, level: AlertLevel = None) -> List[Dict]:
        """获取告警"""
        if level:
            return [a for a in self.alerts if a['level'] == level.value]
        return self.alerts
    
    def clear_alerts(self):
        """清空告警"""
        self.alerts.clear()
```

### 方案3：性能仪表板

```python
# src/presentation/dialogs/performance_dashboard.py

from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                               QLabel, QProgressBar, QTableWidget,
                               QTableWidgetItem, QHeaderView)
from PySide2.QtCore import Qt, QTimer
from src.infrastructure.utils.performance import get_optimizer
from src.infrastructure.monitoring.query_monitor import get_query_monitor

class PerformanceDashboard(QDialog):
    """性能监控仪表板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("性能监控")
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # FPS显示
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_label = QLabel("60")
        self.fps_progress = QProgressBar()
        self.fps_progress.setMaximum(60)
        self.fps_progress.setValue(60)
        fps_layout.addWidget(self.fps_progress)
        layout.addLayout(fps_layout)
        
        # 内存使用
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("内存:"))
        self.memory_label = QLabel("0 MB")
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(2048)
        memory_layout.addWidget(self.memory_progress)
        layout.addLayout(memory_layout)
        
        # 查询统计表格
        self.query_table = QTableWidget()
        self.query_table.setColumnCount(4)
        self.query_table.setHorizontalHeaderLabels(["查询", "次数", "平均时间", "最后执行"])
        self.query_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.query_table)
    
    def setup_timer(self):
        """设置更新定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)  # 每秒更新
    
    def update_stats(self):
        """更新统计数据"""
        optimizer = get_optimizer()
        query_monitor = get_query_monitor()
        
        # 更新FPS
        fps = optimizer.fps_monitor.get_fps()
        self.fps_label.setText(str(fps))
        self.fps_progress.setValue(fps)
        
        # 更新内存
        memory_mb = optimizer.memory_manager.get_memory_usage()
        self.memory_label.setText(f"{memory_mb:.1f} MB")
        self.memory_progress.setValue(int(memory_mb))
        
        # 更新查询统计
        stats = query_monitor.get_query_stats()
        self.query_table.setRowCount(len(stats))
        
        for i, (query, data) in enumerate(stats.items()):
            self.query_table.setItem(i, 0, QTableWidgetItem(query[:50] + "..."))
            self.query_table.setItem(i, 1, QTableWidgetItem(str(data['count'])))
            self.query_table.setItem(i, 2, QTableWidgetItem(f"{data['avg_time']:.3f}s"))
            self.query_table.setItem(i, 3, QTableWidgetItem("-"))
```

---

## 6.5.4 性能监控增强建议

### 立即执行（P0）

| 优化项 | 方案 | 工作量 | 影响 |
|--------|------|--------|------|
| 查询性能监控 | QueryMonitor | 0.5天 | 慢查询分析 |
| 告警规则配置 | AlertManager | 0.5天 | 问题及时发现 |

### 短期执行（P1）

| 优化项 | 方案 | 工作量 | 影响 |
|--------|------|--------|------|
| 性能仪表板 | Dashboard UI | 1天 | 可视化监控 |
| 性能报告生成 | 自动报告 | 0.5天 | 问题追踪 |

### 长期规划（P2）

| 优化项 | 方案 | 工作量 | 影响 |
|--------|------|--------|------|
| 远程监控 | API接口 | 1周 | 远程运维 |
| 机器学习 | 异常检测 | 2周 | 智能告警 |

---

## 6.5.5 性能监控效果预估

| 优化项 | 当前状态 | 优化后 | 提升 |
|--------|---------|--------|------|
| 慢查询发现 | 人工查找 | 自动告警 | +80% |
| 问题定位 | 靠日志分析 | 仪表板可视化 | +60% |
| 性能回归 | 难以发现 | 基准测试 | +70% |

---

## 性能监控讨论记录

| 时间 | 讨论内容 | 结论 |
|------|----------|------|
| 19:40 | 现有性能监控检查 | 发现已有基础框架 |
| 19:45 | 缺失功能分析 | 查询监控和告警最重要 |
| 19:50 | 增强方案讨论 | 确定QueryMonitor+AlertManager方案 |

---

**性能监控讨论状态**：✅ 完成  
**下一步**：性能优化（A项）全部完成总结  
**预计完成时间**：2026年2月11日 20:00:00
