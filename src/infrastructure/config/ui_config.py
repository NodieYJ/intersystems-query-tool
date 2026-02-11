#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI 配置管理模块

用于集中管理 UI 相关的配置，支持：
- 从 JSON 配置文件读取
- 配置验证和默认值
- 配置热重载
- 线程安全的配置访问

配置文件路径: config/ui_config.json
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.data.repositories.driver_factory import DatabaseDriverType

logger = logging.getLogger(__name__)


@dataclass
class ScalingRule:
    """缩放规则数据类"""
    min_width: int
    min_height: int
    scale: float
    name: str
    description: str = ""


@dataclass
class ScalingConfig:
    """缩放配置数据类"""
    rules: List[ScalingRule] = field(default_factory=list)
    default_scale: float = 1.0
    min_scale: float = 0.5
    max_scale: float = 3.0
    auto_detect: bool = True


@dataclass
class DatabaseConfig:
    """数据库配置数据类"""
    driver_priority: List[str] = field(default_factory=lambda: ["iris", "pyodbc"])
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class UIThemeConfig:
    """UI 主题配置数据类"""
    theme: str = "default"
    animations_enabled: bool = True
    font_family: str = "Microsoft YaHei"
    base_font_size: int = 10


@dataclass
class LoggingConfig:
    """日志配置数据类"""
    level: str = "INFO"
    max_file_size_mb: int = 10
    backup_count: int = 10
    console_output: bool = True


class UIConfig:
    """
    UI 配置管理类 - 单例模式
    
    管理所有 UI 相关的配置，支持从 JSON 文件加载和热重载。
    线程安全，可在多线程环境下使用。
    
    使用示例:
        config = UIConfig()
        scale_config = config.get_scaling_config()
        driver_priority = config.get_database_config().driver_priority
    """
    
    _instance: Optional['UIConfig'] = None
    _initialized: bool = False
    _lock: threading.Lock = threading.Lock()
    
    # 默认配置文件路径
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "ui_config.json"
    
    def __new__(cls, config_path: Optional[Union[str, Path]] = None) -> 'UIConfig':
        """线程安全的单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        if UIConfig._initialized:
            return
        
        self._config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self._config_data: Dict[str, Any] = {}
        self._config_lock = threading.RLock()  # 用于配置访问的线程锁
        
        # 加载配置
        self._load_config()
        
        UIConfig._initialized = True
        logger.info(f"UIConfig 初始化完成，配置文件: {self._config_path}")
    
    def _load_config(self) -> None:
        """
        从 JSON 文件加载配置
        
        如果配置文件不存在或解析失败，使用默认配置。
        """
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                logger.info(f"配置文件加载成功: {self._config_path}")
            else:
                logger.warning(f"配置文件不存在: {self._config_path}，使用默认配置")
                self._config_data = self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件解析失败: {e}，使用默认配置")
            self._config_data = self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件时发生错误: {e}，使用默认配置")
            self._config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            "scaling": {
                "rules": [
                    {"min_width": 3200, "min_height": 1800, "scale": 2.0, "name": "3K+", "description": "3K及以上分辨率"},
                    {"min_width": 2560, "min_height": 1440, "scale": 1.5, "name": "2K", "description": "2K分辨率"},
                    {"min_width": 0, "min_height": 0, "scale": 1.0, "name": "1K", "description": "1K及以下分辨率"}
                ],
                "default_scale": 1.0,
                "min_scale": 0.5,
                "max_scale": 3.0,
                "auto_detect": True
            },
            "database": {
                "driver_priority": ["iris", "pyodbc"],
                "connection_timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 1.0
            },
            "ui": {
                "theme": "default",
                "animations_enabled": True,
                "font_family": "Microsoft YaHei",
                "base_font_size": 10
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 10,
                "console_output": True
            }
        }
    
    def reload_config(self) -> bool:
        """
        热重载配置
        
        重新从配置文件加载配置，无需重启应用程序。
        
        Returns:
            bool: 重载是否成功
        """
        try:
            with self._config_lock:
                self._load_config()
            logger.info("配置热重载成功")
            return True
        except Exception as e:
            logger.error(f"配置热重载失败: {e}")
            return False
    
    def get_scaling_config(self) -> ScalingConfig:
        """
        获取缩放配置
        
        Returns:
            ScalingConfig: 缩放配置对象
        """
        with self._config_lock:
            scaling_data = self._config_data.get("scaling", {})
            
            # 解析缩放规则
            rules_data = scaling_data.get("rules", [])
            rules = [
                ScalingRule(
                    min_width=r.get("min_width", 0),
                    min_height=r.get("min_height", 0),
                    scale=r.get("scale", 1.0),
                    name=r.get("name", "Unknown"),
                    description=r.get("description", "")
                )
                for r in rules_data
            ]
            
            # 按分辨率从高到低排序
            rules.sort(key=lambda x: (x.min_width, x.min_height), reverse=True)
            
            return ScalingConfig(
                rules=rules,
                default_scale=scaling_data.get("default_scale", 1.0),
                min_scale=scaling_data.get("min_scale", 0.5),
                max_scale=scaling_data.get("max_scale", 3.0),
                auto_detect=scaling_data.get("auto_detect", True)
            )
    
    def get_database_config(self) -> DatabaseConfig:
        """
        获取数据库配置
        
        Returns:
            DatabaseConfig: 数据库配置对象
        """
        with self._config_lock:
            db_data = self._config_data.get("database", {})
            
            return DatabaseConfig(
                driver_priority=db_data.get("driver_priority", ["iris", "pyodbc"]),
                connection_timeout=db_data.get("connection_timeout", 30),
                retry_attempts=db_data.get("retry_attempts", 3),
                retry_delay=db_data.get("retry_delay", 1.0)
            )
    
    def get_ui_theme_config(self) -> UIThemeConfig:
        """
        获取 UI 主题配置
        
        Returns:
            UIThemeConfig: UI 主题配置对象
        """
        with self._config_lock:
            ui_data = self._config_data.get("ui", {})
            
            return UIThemeConfig(
                theme=ui_data.get("theme", "default"),
                animations_enabled=ui_data.get("animations_enabled", True),
                font_family=ui_data.get("font_family", "Microsoft YaHei"),
                base_font_size=ui_data.get("base_font_size", 10)
            )
    
    def get_logging_config(self) -> LoggingConfig:
        """
        获取日志配置
        
        Returns:
            LoggingConfig: 日志配置对象
        """
        with self._config_lock:
            logging_data = self._config_data.get("logging", {})
            
            return LoggingConfig(
                level=logging_data.get("level", "INFO"),
                max_file_size_mb=logging_data.get("max_file_size_mb", 10),
                backup_count=logging_data.get("backup_count", 10),
                console_output=logging_data.get("console_output", True)
            )
    
    def get_driver_priority(self) -> List[DatabaseDriverType]:
        """
        获取驱动优先级列表
        
        Returns:
            List[DatabaseDriverType]: 按优先级排序的驱动类型列表
        """
        db_config = self.get_database_config()
        priority = []
        
        for driver_name in db_config.driver_priority:
            try:
                driver_type = DatabaseDriverType(driver_name.lower())
                priority.append(driver_type)
            except ValueError:
                logger.warning(f"未知的驱动类型: {driver_name}")
        
        return priority if priority else [DatabaseDriverType.IRIS, DatabaseDriverType.PYODBC]
    
    def get_scale_for_resolution(self, width: int, height: int) -> float:
        """
        根据分辨率获取对应的缩放比例
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
            
        Returns:
            float: 缩放比例
        """
        scaling_config = self.get_scaling_config()
        
        if not scaling_config.auto_detect:
            return scaling_config.default_scale
        
        # 按优先级匹配规则（已按分辨率从高到低排序）
        for rule in scaling_config.rules:
            if width >= rule.min_width and height >= rule.min_height:
                return rule.scale
        
        return scaling_config.default_scale


# 全局配置实例
_ui_config: Optional[UIConfig] = None
_ui_config_lock = threading.Lock()


def get_ui_config(config_path: Optional[Union[str, Path]] = None) -> UIConfig:
    """
    获取全局 UI 配置实例
    
    Args:
        config_path: 配置文件路径，仅在第一次调用时有效
        
    Returns:
        UIConfig: UI 配置单例实例
    """
    global _ui_config
    
    if _ui_config is None:
        with _ui_config_lock:
            if _ui_config is None:
                _ui_config = UIConfig(config_path)
    
    return _ui_config


def reload_ui_config() -> bool:
    """
    热重载全局 UI 配置
    
    Returns:
        bool: 重载是否成功
    """
    config = get_ui_config()
    return config.reload_config()
