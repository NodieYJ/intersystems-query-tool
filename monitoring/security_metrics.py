#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全监控指标收集器

收集和报告安全相关的监控指标
"""

import time
import threading
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class SecurityMetric:
  """安全指标"""
  name: str
  value: float
  timestamp: str
  labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
  """指标收集器"""

  def __init__(self, flush_interval: int = 60):
    """
    初始化指标收集器

    Args:
        flush_interval: 刷新间隔（秒）
    """
    self.metrics: Dict[str, list] = defaultdict(list)
    self.counters: Dict[str, int] = defaultdict(int)
    self.gauges: Dict[str, float] = defaultdict(float)
    self.flush_interval = flush_interval
    self.lock = threading.Lock()
    
    # 启动刷新线程
    self._running = True
    self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
    self._flush_thread.start()

  def _flush_loop(self) -> None:
    """刷新循环"""
    while self._running:
      time.sleep(self.flush_interval)
      self.flush()

  def stop(self) -> None:
    """停止收集器"""
    self._running = False
    self.flush()

  def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
    """增加计数器"""
    with self.lock:
      key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
      self.counters[key] += value

  def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """设置仪表值"""
    with self.lock:
      key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
      self.gauges[key] = value

  def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """记录直方图值"""
    with self.lock:
      key = f"{name}:{json.dumps(labels or {}, sort_keys=True)}"
      self.metrics[key].append(value)

  def flush(self) -> Dict[str, Any]:
    """刷新指标"""
    with self.lock:
      # 收集计数器
      counter_metrics = []
      for key, value in self.counters.items():
        name, labels_str = key.split(":", 1)
        labels = json.loads(labels_str)
        counter_metrics.append(SecurityMetric(
          name=name,
          value=value,
          timestamp=datetime.now().isoformat(),
          labels=labels
        ))
      self.counters.clear()
      
      # 收集仪表
      gauge_metrics = []
      for key, value in self.gauges.items():
        name, labels_str = key.split(":", 1)
        labels = json.loads(labels_str)
        gauge_metrics.append(SecurityMetric(
          name=name,
          value=value,
          timestamp=datetime.now().isoformat(),
          labels=labels
        ))
      
      # 收集直方图
      histogram_metrics = []
      for key, values in self.metrics.items():
        if values:
          name, labels_str = key.split(":", 1)
          labels = json.loads(labels_str)
          histogram_metrics.append({
            "name": name,
            "labels": labels,
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "timestamp": datetime.now().isoformat()
          })
      self.metrics.clear()
      
      result = {
        "timestamp": datetime.now().isoformat(),
        "counters": [asdict(m) for m in counter_metrics],
        "gauges": [asdict(m) for m in gauge_metrics],
        "histograms": histogram_metrics
      }
      
      return result

  def get_summary(self) -> Dict[str, Any]:
    """获取指标摘要"""
    result = self.flush()
    return {
      "total_counters": len(result["counters"]),
      "total_gauges": len(result["gauges"]),
      "total_histograms": len(result["histograms"]),
      "timestamp": result["timestamp"]
    }


# 创建全局指标收集器
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
  """获取指标收集器实例"""
  return metrics_collector


# 便捷函数
def record_login_attempt(success: bool, user_id: Optional[str] = None) -> None:
  """记录登录尝试"""
  collector = get_metrics_collector()
  collector.increment_counter(
    "login_attempts_total",
    labels={"result": "success" if success else "failed"}
  )
  if user_id:
    collector.increment_counter(
      "login_attempts_by_user",
      labels={"user_id": user_id, "result": "success" if success else "failed"}
    )


def record_sql_injection_attempt(ip_address: str) -> None:
  """记录 SQL 注入尝试"""
  collector = get_metrics_collector()
  collector.increment_counter(
    "sql_injection_attempts_total",
    labels={"ip": ip_address}
  )


def record_password_strength(score: int) -> None:
  """记录密码强度"""
  collector = get_metrics_collector()
  strength_level = "weak" if score < 3 else "medium" if score < 5 else "strong"
  collector.increment_counter(
    "password_strength_distribution",
    labels={"level": strength_level}
  )
  collector.record_histogram(
    "password_strength_score",
    score,
    labels={"level": strength_level}
  )


def record_rate_limit_hit(client_id: str) -> None:
  """记录速率限制命中"""
  collector = get_metrics_collector()
  collector.increment_counter(
    "rate_limit_hits_total",
    labels={"client_id": client_id[:8]}  # 脱敏
  )


def record_query_validation(result: bool, query_type: str) -> None:
  """记录查询验证结果"""
  collector = get_metrics_collector()
  collector.increment_counter(
    "query_validation_total",
    labels={"result": "allowed" if result else "blocked", "type": query_type}
  )
