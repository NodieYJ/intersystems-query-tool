#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
性能优化工具模块
包含UI渲染优化、内存管理和事件处理优化
"""

import weakref
import time
from PySide2.QtCore import Qt, QObject, QTimer, QEvent
from PySide2.QtWidgets import QApplication

class EventCompressor(QObject):
    """事件压缩器，用于减少频繁事件的处理开销"""
    def __init__(self, parent=None, timeout=100):
        super().__init__(parent)
        self.timeout = timeout  # 超时时间（毫秒）
        self.events = []  # 存储事件
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.process_events)
    
    def add_event(self, event):
        """添加事件"""
        self.events.append(event)
        if not self.timer.isActive():
            self.timer.start(self.timeout)
    
    def process_events(self):
        """处理事件"""
        if self.events:
            # 批量处理事件
            events = self.events.copy()
            self.events.clear()
            self.handle_events(events)
    
    def handle_events(self, events):
        """处理事件的回调方法，子类实现"""
        pass

class MemoryManager:
    """内存管理器，用于优化内存使用"""
    def __init__(self):
        self.objects = weakref.WeakValueDictionary()
        self.counter = 0
    
    def register_object(self, obj, name=None):
        """注册对象"""
        if name is None:
            name = f"obj_{self.counter}"
            self.counter += 1
        self.objects[name] = obj
        return name
    
    def get_object(self, name):
        """获取对象"""
        return self.objects.get(name)
    
    def clear_unused(self):
        """清理未使用的对象"""
        # WeakValueDictionary会自动清理垃圾回收的对象
        pass
    
    def get_stats(self):
        """获取内存统计信息"""
        return {
            "object_count": len(self.objects),
            "object_keys": list(self.objects.keys())
        }

class DeferredUpdater(QObject):
    """延迟更新器，用于减少频繁的UI更新"""
    def __init__(self, parent=None, delay=50):
        super().__init__(parent)
        self.delay = delay
        self.pending_updates = {}
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.perform_updates)
    
    def schedule_update(self, key, update_func, *args, **kwargs):
        """安排更新"""
        self.pending_updates[key] = (update_func, args, kwargs)
        if not self.timer.isActive():
            self.timer.start(self.delay)
    
    def perform_updates(self):
        """执行更新"""
        if self.pending_updates:
            updates = self.pending_updates.copy()
            self.pending_updates.clear()
            for key, (func, args, kwargs) in updates.items():
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    print(f"更新失败 ({key}): {e}")

class FPSMonitor(QObject):
    """FPS监视器，用于监控UI渲染性能"""
    def __init__(self, parent=None, interval=1000):
        super().__init__(parent)
        self.interval = interval  # 监控间隔（毫秒）
        self.frame_count = 0
        self.last_time = time.time()
        self.current_fps = 0
        self.event_filter_installed = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_fps)
        
    def start_monitoring(self):
        """开始监控"""
        self.timer.start(self.interval)
        # 安装事件过滤器
        app = QApplication.instance()
        if app and not self.event_filter_installed:
            app.installEventFilter(self)
            self.event_filter_installed = True
    
    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
        # 移除事件过滤器
        app = QApplication.instance()
        if app and self.event_filter_installed:
            app.removeEventFilter(self)
            self.event_filter_installed = False
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        if event.type() == QEvent.Paint:
            self.frame_count += 1
        return super().eventFilter(obj, event)
    
    def update_fps(self):
        """更新FPS"""
        current_time = time.time()
        elapsed = current_time - self.last_time
        self.current_fps = self.frame_count / elapsed
        self.last_time = current_time
        self.frame_count = 0
        # 可以在这里添加回调，通知UI更新FPS显示
    
    def get_fps(self):
        """获取当前FPS"""
        return self.current_fps

class VirtualListModel(QObject):
    """虚拟列表模型，用于处理大量数据的显示"""
    def __init__(self, parent=None, data_provider=None):
        super().__init__(parent)
        self.data_provider = data_provider  # 数据提供者，返回指定范围内的数据
        self.total_items = 0
        self.cache = {}
        self.cache_size = 100  # 缓存大小
    
    def set_data_provider(self, provider):
        """设置数据提供者"""
        self.data_provider = provider
    
    def set_total_items(self, count):
        """设置总项目数"""
        self.total_items = count
    
    def get_item(self, index):
        """获取指定索引的项目"""
        if index < 0 or index >= self.total_items:
            return None
        
        # 检查缓存
        if index in self.cache:
            return self.cache[index]
        
        # 从数据提供者获取数据
        if self.data_provider:
            data = self.data_provider(index, index + 1)
            if data:
                self.cache[index] = data[0]
                # 清理缓存
                self._clean_cache()
                return data[0]
        
        return None
    
    def get_items(self, start, end):
        """获取指定范围的项目"""
        items = []
        for i in range(start, min(end, self.total_items)):
            item = self.get_item(i)
            if item:
                items.append(item)
        return items
    
    def _clean_cache(self):
        """清理缓存"""
        if len(self.cache) > self.cache_size:
            # 只保留最近使用的项目
            keys = sorted(self.cache.keys())
            for key in keys[:-self.cache_size]:
                del self.cache[key]

class PerformanceOptimizer:
    """性能优化器，整合各种优化工具"""
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.deferred_updater = DeferredUpdater()
        self.fps_monitor = FPSMonitor()
        self.event_compressors = {}
        self.is_initialized = False
    
    def initialize(self):
        """初始化性能优化器"""
        if not self.is_initialized:
            self.fps_monitor.start_monitoring()
            self.is_initialized = True
    
    def shutdown(self):
        """关闭性能优化器"""
        if self.is_initialized:
            self.fps_monitor.stop_monitoring()
            self.is_initialized = False
    
    def get_memory_manager(self):
        """获取内存管理器"""
        return self.memory_manager
    
    def get_deferred_updater(self):
        """获取延迟更新器"""
        return self.deferred_updater
    
    def get_fps_monitor(self):
        """获取FPS监视器"""
        return self.fps_monitor
    
    def create_event_compressor(self, name, timeout=100):
        """创建事件压缩器"""
        compressor = EventCompressor(timeout=timeout)
        self.event_compressors[name] = compressor
        return compressor
    
    def get_event_compressor(self, name):
        """获取事件压缩器"""
        return self.event_compressors.get(name)
    
    def get_performance_stats(self):
        """获取性能统计信息"""
        return {
            "fps": self.fps_monitor.get_fps(),
            "memory": self.memory_manager.get_stats(),
            "event_compressors": list(self.event_compressors.keys())
        }

# 全局性能优化器实例
optimizer = PerformanceOptimizer()

def get_optimizer():
    """获取全局性能优化器实例"""
    return optimizer
