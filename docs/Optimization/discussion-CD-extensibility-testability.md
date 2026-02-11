# 深入讨论：可扩展性优化

**讨论时间**：2026年2月11日 22:10:00  
**参与人员**：AI Assistant + 用户

---

## 一、当前可扩展性现状分析

### 1.1 现有可扩展性机制

```python
# 当前实现的事件压缩器
class EventCompressor:
    def __init__(self, parent=None, timeout=100):
        self.timeout = timeout
        self.events = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_events)
    
    def add_event(self, event):
        self.events.append(event)
        if not self.timer.isActive():
            self.timer.start(self.timeout)
    
    def process_events(self):
        # 批量处理事件
        pass
```

### 1.2 问题清单

| # | 问题 | 影响 | 严重程度 |
|---|------|------|----------|
| **1** | 无插件系统 | 无法扩展功能 | 🔴 高 |
| **2** | 无事件总线 | 组件紧耦合 | 🟡 中 |
| **3** | 缺少策略模式 | 变体逻辑难扩展 | 🟡 中 |
| **4** | 无配置扩展点 | 新配置困难 | 🟡 低 |

### 1.3 当前架构问题

```
UI层 → 直接调用 → 业务层 → 直接调用 → 数据层
         ↓
    无法动态扩展
```

---

## 二、解决方案：可扩展性架构设计

### 2.1 插件系统设计

```python
# src/infrastructure/ext/plugin_system.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from enum import Enum
import importlib
import os
import sys

class PluginState(Enum):
    """插件状态"""
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"
    DISABLED = "disabled"

class IPlugin(ABC):
    """插件接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass
    
    @abstractmethod
    def initialize(self, context: 'PluginContext') -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行插件功能"""
        pass
    
    def cleanup(self):
        """清理资源（可选）"""
        pass

class PluginContext:
    """插件上下文"""
    
    def __init__(self, app_container):
        self.container = app_container
        self.config = app_container.config
        self.logger = app_container.logger
        self.event_bus = app_container.event_bus
    
    def get_service(self, service_type: Type):
        """获取服务"""
        return self.container.get(service_type)

class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, IPlugin] = {}
        self._hooks: Dict[str, List[callable]] = {}
        self._instance = None
    
    def discover_plugins(self) -> List[str]:
        """发现插件"""
        plugin_paths = []
        if os.path.exists(self.plugin_dir):
            for filename in os.listdir(self.plugin_dir):
                if filename.endswith('.py') and not filename.startswith('_'):
                    plugin_paths.append(filename[:-3])
        return plugin_paths
    
    def load_plugin(self, plugin_class: Type[IPlugin]) -> bool:
        """加载插件"""
        try:
            plugin = plugin_class()
            if plugin.initialize(self._context):
                self._plugins[plugin.name] = plugin
                return True
            return False
        except Exception as e:
            logger.error(f"加载插件失败: {plugin_class.__name__}: {e}")
            return False
    
    def register_hook(self, hook_name: str, callback: callable):
        """注册钩子"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
    
    def trigger_hook(self, hook_name: str, **kwargs):
        """触发钩子"""
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                callback(**kwargs)
```

### 2.2 事件驱动架构

```python
# src/infrastructure/events/event_bus.py

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import uuid

class EventType(Enum):
    """事件类型"""
    QUERY_STARTED = "query_started"
    QUERY_COMPLETED = "query_completed"
    QUERY_FAILED = "query_failed"
    DATA_LOADED = "data_loaded"
    UI_THEME_CHANGED = "ui_theme_changed"
    CONFIG_CHANGED = "config_changed"
    CONNECTION_LOST = "connection_lost"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

@dataclass
class Event:
    """事件"""
    id: str
    type: EventType
    payload: Dict[str, Any]
    timestamp: datetime
    source: str
    
    @classmethod
    def create(cls, event_type: EventType, source: str, payload: Dict = None):
        return cls(
            id=str(uuid.uuid4()),
            type=event_type,
            payload=payload or {},
            timestamp=datetime.now(),
            source=source
        )

class IEventBus(ABC):
    """事件总线接口"""
    
    @abstractmethod
    def subscribe(self, event_type: EventType, callback: Callable) -> str:
        """订阅事件"""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        pass
    
    @abstractmethod
    def publish(self, event: Event):
        """发布事件"""
        pass
    
    @abstractmethod
    def get_subscribers(self, event_type: EventType) -> List[Callable]:
        """获取订阅者"""
        pass

class EventBus(IEventBus):
    """事件总线实现"""
    
    def __init__(self):
        self._subscriptions: Dict[str, Dict] = {}
        self._subscribers: Dict[EventType, List[Dict]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._lock = __import__('threading').Lock()
    
    def subscribe(self, event_type: EventType, callback: Callable) -> str:
        """订阅事件"""
        sub_id = str(uuid.uuid4())
        
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append({
            'id': sub_id,
            'callback': callback
        })
        
        self._subscriptions[sub_id] = {
            'event_type': event_type,
            'callback': callback
        }
        
        return sub_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        if subscription_id in self._subscriptions:
            sub = self._subscriptions[subscription_id]
            event_type = sub['event_type']
            
            if event_type in self._subscribers:
                self._subscribers[event_type] = [
                    s for s in self._subscribers[event_type]
                    if s['id'] != subscription_id
                ]
            
            del self._subscriptions[subscription_id]
            return True
        return False
    
    def publish(self, event: Event):
        """发布事件"""
        with self._lock:
            # 添加到历史
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history = self._event_history[-self._max_history:]
            
            # 通知订阅者
            if event.type in self._subscribers:
                for subscriber in self._subscribers[event.type]:
                    try:
                        subscriber['callback'](event)
                    except Exception as e:
                        logger.error(f"事件处理失败: {event.type}: {e}")
    
    def get_subscribers(self, event_type: EventType) -> List[Callable]:
        """获取订阅者"""
        if event_type in self._subscribers:
            return [s['callback'] for s in self._subscribers[event_type]]
        return []
    
    def get_event_history(self, event_type: EventType = None) -> List[Event]:
        """获取事件历史"""
        if event_type:
            return [e for e in self._event_history if e.type == event_type]
        return list(self._event_history)
```

### 2.3 策略模式扩展

```python
# src/infrastructure/strategy/strategy_pattern.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum

class StrategyPriority(Enum):
    """策略优先级"""
    HIGH = 0
    MEDIUM = 1
    LOW = 2

class IStrategy(ABC):
    """策略接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> StrategyPriority:
        """策略优先级"""
        pass
    
    @abstractmethod
    def can_handle(self, context: Dict) -> bool:
        """是否能处理"""
        pass
    
    @abstractmethod
    def execute(self, context: Dict) -> Any:
        """执行策略"""
        pass

class StrategyContext:
    """策略上下文"""
    
    def __init__(self):
        self.data = {}
        self.strategies: List[IStrategy] = []
    
    def add_strategy(self, strategy: IStrategy):
        """添加策略"""
        self.strategies.append(strategy)
        # 按优先级排序
        self.strategies.sort(key=lambda s: s.priority.value)
    
    def execute(self) -> Any:
        """执行策略"""
        for strategy in self.strategies:
            if strategy.can_handle(self.data):
                return strategy.execute(self.data)
        raise ValueError("没有可用的策略")

# 示例：查询策略
class QueryStrategy(IStrategy):
    """查询策略"""
    
    def __init__(self):
        self._priority = StrategyPriority.MEDIUM
    
    @property
    def name(self) -> str:
        return "QueryStrategy"
    
    @property
    def priority(self) -> StrategyPriority:
        return self._priority
    
    def can_handle(self, context: Dict) -> bool:
        return 'query' in context
    
    def execute(self, context: Dict) -> Any:
        return f"执行查询: {context['query']}"
```

---

## 三、测试性优化讨论

### 3.1 当前测试现状

| 指标 | 当前值 | 问题 |
|------|--------|------|
| 测试覆盖率 | 80% | UI层覆盖率低 |
| Mock能力 | 困难 | 无统一Mock工厂 |
| 测试速度 | 慢 | 缺少并行测试 |
| 测试数据 | 手工 | 缺少数据工厂 |

### 3.2 Mock体系设计

```python
# src/infrastructure/testing/mock_factory.py

from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, Type

class MockFactory:
    """Mock工厂"""
    
    @staticmethod
    def create_repository() -> Mock:
        mock = Mock()
        mock.execute_query.return_value = []
        mock.execute_non_query.return_value = True
        return mock
    
    @staticmethod
    def create_config() -> Mock:
        mock = Mock()
        mock.get.side_effect = lambda key, default=None: {
            'database.host': 'localhost',
            'database.port': 1972,
        }.get(key, default)
        return mock
    
    @staticmethod
    def create_logger() -> Mock:
        return Mock()

class MockRegistry:
    """Mock注册中心"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mocks = {}
        return cls._instance
    
    def register(self, name: str, mock_obj: Any):
        self._mocks[name] = mock_obj
    
    def get(self, name: str) -> Any:
        return self._mocks.get(name)
```

---

## 四、讨论总结

### C) 可扩展性 - 优化项

| 方案 | 工作量 | 优先级 | 收益 |
|------|--------|--------|------|
| 插件系统设计 | 高 | P1 | 高 |
| 事件驱动架构 | 中 | P1 | 高 |
| 策略模式 | 中 | P2 | 中 |

### D) 测试性 - 优化项

| 方案 | 工作量 | 优先级 | 收益 |
|------|--------|--------|------|
| Mock工厂 | 中 | P0 | 高 |
| pytest迁移 | 中 | P1 | 中 |
| 测试数据工厂 | 中 | P1 | 中 |

---

**讨论状态**：✅ C和D优化项初步分析完成  
**文档已保存**：`docs/Optimization/discussion-CD-extensibility-testability.md`  
**下一步**：需要继续深入讨论请告知具体方面