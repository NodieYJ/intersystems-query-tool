# 深入讨论：可扩展性 - 插件系统详细设计

**讨论时间**：2026年2月11日 22:20:00  
**参与人员**：AI Assistant + 用户

---

## 一、插件系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    插件系统架构                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ PluginManager│  │HookManager │  │ExtensionPoint│    │
│  │  插件管理器   │  │  钩子管理器  │  │   扩展点    │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                 │                 │            │
│         └────────────────┼─────────────────┘            │
│                          │                              │
│         ┌────────────────┼─────────────────┐            │
│         │                 │                 │            │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐   │
│  │  UI插件      │  │ 数据插件      │  │  功能插件    │   │
│  │ (主题/菜单)  │  │ (新数据源)   │  │ (导出/分析) │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 1.2 核心接口定义

```python
# src/infrastructure/ext/plugin_interface.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from enum import Enum
from dataclasses import dataclass

class PluginType(Enum):
    """插件类型"""
    UI = "ui"              # UI相关插件
    DATA = "data"           # 数据源插件
    FUNCTION = "function"   # 功能扩展插件
    THEME = "theme"        # 主题插件

class PluginStatus(Enum):
    """插件状态"""
    DISABLED = "disabled"
    ENABLED = "enabled"
    LOADED = "loaded"
    ERROR = "error"

@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    min_version: str = None  # 最小应用版本

class IPlugin(ABC):
    """插件接口基类"""
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """获取插件信息"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> PluginStatus:
        """获取插件状态"""
        pass
    
    @abstractmethod
    def install(self, context: 'PluginContext') -> bool:
        """安装插件"""
        pass
    
    @abstractmethod
    def uninstall(self) -> bool:
        """卸载插件"""
        pass
    
    @abstractmethod
    def enable(self) -> bool:
        """启用插件"""
        pass
    
    @abstractmethod
    def disable(self) -> bool:
        """禁用插件"""
        pass

class IUIPlugin(IPlugin):
    """UI插件接口"""
    
    @abstractmethod
    def register_actions(self, menu_registry: 'MenuRegistry') -> List['UIAction']:
        """注册菜单动作"""
        pass
    
    @abstractmethod
    def register_widgets(self, widget_registry: 'WidgetRegistry') -> List['UIWidget']:
        """注册小部件"""
        pass

class IDataPlugin(IPlugin):
    """数据源插件接口"""
    
    @abstractmethod
    def get_data_source_type(self) -> str:
        """获取数据源类型"""
        pass
    
    @abstractmethod
    def create_connection(self, config: Dict) -> 'IDataConnection':
        """创建数据源连接"""
        pass

class IFunctionPlugin(IPlugin):
    """功能插件接口"""
    
    @abstractmethod
    def get_functions(self) -> List['PluginFunction']:
        """获取提供的功能列表"""
        pass
    
    @abstractmethod
    def execute_function(self, func_name: str, **kwargs) -> Any:
        """执行功能"""
        pass
```

### 1.3 插件管理器详细实现

```python
# src/infrastructure/ext/plugin_manager.py

import os
import sys
import importlib
import inspect
from typing import Dict, List, Optional, Type
from pathlib import Path

class PluginManager:
    """插件管理器"""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self._plugins: Dict[str, IPlugin] = {}
        self._plugin_classes: Dict[str, Type[IPlugin]] = {}
        self._context: Optional['PluginContext'] = None
        self._hook_manager = HookManager()
        self._extension_registry = ExtensionRegistry()
    
    def set_context(self, context: 'PluginContext'):
        """设置插件上下文"""
        self._context = context
    
    def discover_plugins(self) -> List[str]:
        """发现插件"""
        plugin_names = []
        
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True, exist_ok=True)
            return []
        
        # 扫描插件目录
        for filepath in self.plugin_dir.glob("*.py"):
            if filepath.name.startswith("_"):
                continue
            
            module_name = filepath.stem
            
            # 检查是否是有效插件模块
            if self._is_plugin_module(module_name):
                plugin_names.append(module_name)
        
        return plugin_names
    
    def _is_plugin_module(self, module_name: str) -> bool:
        """检查模块是否是插件"""
        try:
            module = importlib.import_module(f"plugins.{module_name}")
            
            # 检查是否有插件类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, IPlugin) and 
                    obj != IPlugin):
                    return True
            return False
        except ImportError:
            return False
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件"""
        try:
            # 导入模块
            module = importlib.import_module(f"plugins.{plugin_name}")
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, IPlugin) and 
                    obj != IPlugin):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error(f"模块 {plugin_name} 中未找到插件类")
                return False
            
            # 创建插件实例
            plugin = plugin_class()
            
            # 安装插件
            if plugin.install(self._context):
                self._plugins[plugin_name] = plugin
                self._plugin_classes[plugin_name] = plugin_class
                logger.info(f"插件 {plugin_name} 已加载")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"加载插件 {plugin_name} 失败: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            
            try:
                plugin.uninstall()
                del self._plugins[plugin_name]
                logger.info(f"插件 {plugin_name} 已卸载")
                return True
            except Exception as e:
                logger.error(f"卸载插件 {plugin_name} 失败: {e}")
                return False
        return False
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        if plugin_name in self._plugins:
            if self._plugins[plugin_name].enable():
                self._hook_manager.register_plugin_hooks(
                    plugin_name, 
                    self._plugins[plugin_name]
                )
                return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        if plugin_name in self._plugins:
            self._hook_manager.unregister_plugin_hooks(plugin_name)
            return self._plugins[plugin_name].disable()
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件"""
        return self._plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[IPlugin]:
        """获取指定类型的插件"""
        return [
            p for p in self._plugins.values()
            if p.info.plugin_type == plugin_type
        ]
    
    def reload_all_plugins(self):
        """重新加载所有插件"""
        for plugin_name in list(self._plugins.keys()):
            self.unload_plugin(plugin_name)
        
        for plugin_name in self.discover_plugins():
            self.load_plugin(plugin_name)
```

### 1.4 钩子系统

```python
# src/infrastructure/ext/hook_manager.py

from typing import Any, Callable, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

class HookType(Enum):
    """钩子类型"""
    BEFORE_QUERY = "before_query"
    AFTER_QUERY = "after_query"
    BEFORE_EXPORT = "before_export"
    AFTER_EXPORT = "after_export"
    ON_APP_START = "on_app_start"
    ON_APP_EXIT = "on_app_exit"
    ON_DATA_LOAD = "on_data_load"
    ON_UI_READY = "on_ui_ready"

@dataclass
class Hook:
    """钩子定义"""
    hook_type: HookType
    callback: Callable
    plugin_name: str
    priority: int = 0  # 优先级，数值越小越先执行

class HookManager:
    """钩子管理器"""
    
    def __init__(self):
        self._hooks: Dict[HookType, List[Hook]] = {}
        self._plugin_hooks: Dict[str, List[HookType]] = {}
    
    def register_hook(
        self,
        hook_type: HookType,
        callback: Callable,
        plugin_name: str,
        priority: int = 0
    ) -> bool:
        """注册钩子"""
        hook = Hook(
            hook_type=hook_type,
            callback=callback,
            plugin_name=plugin_name,
            priority=priority
        )
        
        if hook_type not in self._hooks:
            self._hooks[hook_type] = []
        
        self._hooks[hook_type].append(hook)
        
        # 按优先级排序
        self._hooks[hook_type].sort(key=lambda h: h.priority)
        
        # 记录插件的钩子
        if plugin_name not in self._plugin_hooks:
            self._plugin_hooks[plugin_name] = []
        self._plugin_hooks[plugin_name].append(hook_type)
        
        return True
    
    def unregister_plugin_hooks(self, plugin_name: str):
        """取消注册插件的所有钩子"""
        if plugin_name in self._plugin_hooks:
            for hook_type in self._plugin_hooks[plugin_name]:
                if hook_type in self._hooks:
                    self._hooks[hook_type] = [
                        h for h in self._hooks[hook_type]
                        if h.plugin_name != plugin_name
                    ]
            
            del self._plugin_hooks[plugin_name]
    
    def execute_hooks(self, hook_type: HookType, **kwargs) -> Dict[str, Any]:
        """执行指定类型的所有钩子"""
        results = {}
        
        if hook_type in self._hooks:
            for hook in self._hooks[hook_type]:
                try:
                    result = hook.callback(**kwargs)
                    results[hook.plugin_name] = result
                except Exception as e:
                    logger.error(
                        f"执行钩子 {hook_type} 失败 "
                        f"(插件: {hook.plugin_name}): {e}"
                    )
        
        return results
    
    def get_hooks_for_type(self, hook_type: HookType) -> List[Hook]:
        """获取指定类型的钩子"""
        return self._hooks.get(hook_type, [])
```

### 1.5 扩展点系统

```python
# src/infrastructure/ext/extension_point.py

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from enum import Enum

class ExtensionPointType(Enum):
    """扩展点类型"""
    MENU = "menu"
    TOOLBAR = "toolbar"
    DATA_SOURCE = "data_source"
    EXPORT_FORMAT = "export_format"
    IMPORT_FORMAT = "import_format"
    ANALYSIS_TOOL = "analysis_tool"

class ExtensionRegistry:
    """扩展注册表"""
    
    def __init__(self):
        self._extension_points: Dict[str, 'ExtensionPoint'] = {}
        self._extensions: Dict[str, List[Dict]] = {}
    
    def register_extension_point(self, point: 'ExtensionPoint'):
        """注册扩展点"""
        self._extension_points[point.id] = point
        self._extensions[point.id] = []
    
    def register_extension(
        self,
        point_id: str,
        extension_id: str,
        extension_data: Dict
    ) -> bool:
        """注册扩展"""
        if point_id not in self._extension_points:
            logger.error(f"扩展点 {point_id} 不存在")
            return False
        
        self._extensions[point_id].append({
            'id': extension_id,
            'data': extension_data
        })
        return True
    
    def get_extensions(self, point_id: str) -> List[Dict]:
        """获取扩展点所有扩展"""
        return self._extensions.get(point_id, [])
    
    def get_extension_point(self, point_id: str) -> Optional['ExtensionPoint']:
        """获取扩展点"""
        return self._extension_points.get(point_id)

class ExtensionPoint(ABC):
    """扩展点基类"""
    
    def __init__(self, point_id: str, name: str, point_type: ExtensionPointType):
        self.id = point_id
        self.name = name
        self.point_type = point_type
    
    @abstractmethod
    def get_extensions(self) -> List[Dict]:
        """获取扩展列表"""
        pass
    
    @abstractmethod
    def validate_extension(self, extension: Dict) -> bool:
        """验证扩展有效性"""
        pass
```

### 1.6 示例：创建自定义插件

```python
# plugins/example_plugin.py

from src.infrastructure.ext.plugin_interface import (
    IPlugin, PluginInfo, PluginType, PluginStatus
)

class ExamplePlugin(IPlugin):
    """示例插件"""
    
    def __init__(self):
        self._status = PluginStatus.DISABLED
        self._context = None
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="example_plugin",
            version="1.0.0",
            description="这是一个示例插件",
            author="Developer",
            plugin_type=PluginType.FUNCTION,
            dependencies=[]
        )
    
    @property
    def status(self) -> PluginStatus:
        return self._status
    
    def install(self, context) -> bool:
        """安装插件"""
        self._context = context
        
        # 注册扩展
        context.extension_registry.register_extension(
            point_id="analysis_tools",
            extension_id="example_tool",
            extension_data={
                'name': '示例工具',
                'description': '这是一个示例分析工具',
                'function': self.example_function
            }
        )
        
        # 注册钩子
        context.hook_manager.register_hook(
            hook_type=HookType.AFTER_QUERY,
            callback=self.on_after_query,
            plugin_name="example_plugin",
            priority=10
        )
        
        return True
    
    def uninstall(self) -> bool:
        """卸载插件"""
        self._status = PluginStatus.DISABLED
        return True
    
    def enable(self) -> bool:
        """启用插件"""
        self._status = PluginStatus.ENABLED
        return True
    
    def disable(self) -> bool:
        """禁用插件"""
        self._status = PluginStatus.DISABLED
        return True
    
    def example_function(self, data: Any) -> Dict:
        """示例功能"""
        return {'result': f'处理了 {data}'}
    
    def on_after_query(self, query: str, result: Any):
        """查询完成后执行的钩子"""
        print(f"查询完成: {query[:50]}...")
```

---

## 二、插件系统使用场景

### 2.1 UI扩展

```python
# 插件注册自定义菜单
class UIMenuPlugin(IPlugin):
    def register_actions(self, menu_registry):
        return [
            UIAction(
                id="custom_menu_action",
                text="自定义功能",
                icon="custom.png",
                handler=self.custom_action_handler
            )
        ]
```

### 2.2 数据源扩展

```python
# 插件添加新数据源
class CSVDataPlugin(IDataPlugin):
    def get_data_source_type(self) -> str:
        return "csv"
    
    def create_connection(self, config: Dict):
        return CSVConnection(config['filepath'])
```

### 2.3 功能扩展

```python
# 插件添加新功能
class ExportPlugin(IFunctionPlugin):
    def get_functions(self) -> List[PluginFunction]:
        return [
            PluginFunction(
                id="export_pdf",
                name="导出PDF",
                description="将数据导出为PDF格式"
            )
        ]
```

---

## 三、插件系统集成

### 3.1 与DI容器集成

```python
# src/infrastructure/di/container.py 扩展

class DIContainer:
    def setup(self):
        # 注册插件管理器
        self.register(PluginManager)
        
        # 注册钩子管理器
        self.register(HookManager)
        
        # 注册扩展注册表
        self.register(ExtensionRegistry)
    
    def initialize_plugins(self):
        """初始化所有插件"""
        plugin_manager = self.get(PluginManager)
        plugin_manager.set_context(self)
        
        # 发现并加载插件
        for plugin_name in plugin_manager.discover_plugins():
            if plugin_manager.load_plugin(plugin_name):
                plugin_manager.enable_plugin(plugin_name)
```

### 3.2 在主窗口中使用插件

```python
# src/presentation/windows/main_window.py

class MainWindow:
    def __init__(self):
        self.plugin_manager = get_plugin_manager()
        self._setup_plugin_menus()
        self._setup_plugin_hooks()
    
    def _setup_plugin_menus(self):
        """设置插件菜单"""
        ui_plugins = self.plugin_manager.get_plugins_by_type(PluginType.UI)
        
        for plugin in ui_plugins:
            if isinstance(plugin, IUIPlugin):
                actions = plugin.register_actions(self.menu_registry)
                self.menu_registry.add_actions(actions)
    
    def _setup_plugin_hooks(self):
        """设置插件钩子"""
        self.plugin_manager._hook_manager.register_hook(
            HookType.ON_APP_START,
            callback=self._on_app_start,
            plugin_name="system",
            priority=0
        )
```

---

## 四、插件系统实施计划

### 4.1 阶段1：核心框架（1周）

| 任务 | 工作量 | 负责人 |
|------|--------|--------|
| 插件接口定义 | 1天 | AI |
| 插件管理器实现 | 2天 | AI |
| 钩子系统实现 | 1天 | AI |
| 扩展点系统实现 | 1天 | AI |

### 4.2 阶段2：示例插件（0.5周）

| 任务 | 工作量 | 负责人 |
|------|--------|--------|
| 创建示例插件 | 0.5天 | AI |
| 编写插件开发文档 | 0.5天 | AI |

### 4.3 阶段3：集成测试（0.5周）

| 任务 | 工作量 | 负责人 |
|------|--------|--------|
| 插件单元测试 | 0.5天 | AI |
| 集成测试 | 0.5天 | AI |

---

## 五、预期效果

| 指标 | 当前 | 优化后 | 提升 |
|------|------|--------|------|
| **功能扩展能力** | 无 | 插件化 | N/A |
| **第三方开发** | 困难 | 简单 | +200% |
| **模块化程度** | 低 | 高 | +150% |
| **新功能开发速度** | 慢 | 快 | +50% |

---

**讨论状态**：✅ 插件系统详细设计完成  
**下一步**：继续讨论事件驱动架构详细设计
