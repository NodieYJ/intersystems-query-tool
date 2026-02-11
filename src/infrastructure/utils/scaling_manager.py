#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缩放管理器模块

用于集中管理应用程序的 UI 缩放比例，支持根据屏幕分辨率自动计算缩放比例。
基于 UI/UX Pro Max 设计系统。
"""

import logging
import threading
from typing import Optional

from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QScreen

# 导入配置管理器
try:
    from src.infrastructure.config.ui_config import get_ui_config, ScalingRule
    _config_available = True
except ImportError:
    _config_available = False
    logger = logging.getLogger(__name__)
    logger.warning("UIConfig 不可用，使用默认缩放规则")

logger = logging.getLogger(__name__)


class ScalingManager:
    """
    缩放管理器类 - 单例模式
    
    管理应用程序的 UI 缩放比例，支持：
    - 根据屏幕分辨率自动计算缩放比例
    - 手动设置缩放比例
    - 提供缩放计算工具方法
    
    缩放规则：
    - ≤1920x1080 (1K及以下): 100% 缩放 (1.0x)
    - ~2560x1440 (2K): 150% 缩放 (1.5x)
    - ≥3200x1800 (3K及以上): 200% 缩放 (2.0x) - 2倍放大
    
    线程安全：使用双重检查锁定模式确保线程安全
    """
    
    _instance: Optional['ScalingManager'] = None
    _initialized: bool = False
    _lock: threading.Lock = threading.Lock()  # 类级别锁，用于线程安全
    
    def __new__(cls) -> 'ScalingManager':
        """线程安全的单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                # 双重检查：获取锁后再次检查
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.debug("ScalingManager 实例已创建")
        return cls._instance
    
    def __init__(self):
        """初始化缩放管理器（仅执行一次）"""
        if ScalingManager._initialized:
            return
            
        self._scale_factor: float = 1.0
        self._screen_resolution: tuple[int, int] = (1920, 1080)
        self._screen_dpi: float = 96.0
        ScalingManager._initialized = True
        
        logger.debug("ScalingManager 初始化完成")
    
    def calculate_from_screen(self, app: Optional[QApplication] = None) -> float:
        """
        根据屏幕分辨率计算缩放比例
        
        Args:
            app: QApplication 实例，如果为 None 则使用当前应用程序
            
        Returns:
            float: 计算后的缩放比例 (1.0, 1.5, 或 2.0)
        """
        if app is None:
            app = QApplication.instance()  # type: ignore
            
        if app is None:
            logger.warning("无法获取 QApplication 实例，使用默认缩放比例 1.0")
            self._scale_factor = 1.0
            return self._scale_factor
        
        screen = app.primaryScreen()
        if screen is None:
            logger.warning("无法获取屏幕信息，使用默认缩放比例 1.0")
            self._scale_factor = 1.0
            return self._scale_factor
        
        geometry = screen.geometry()
        width = geometry.width()
        height = geometry.height()
        self._screen_resolution = (width, height)
        
        # 获取 DPI 作为辅助判断
        self._screen_dpi = screen.logicalDotsPerInch()
        
        logger.info(f"屏幕分辨率: {width} x {height}, DPI: {self._screen_dpi}")
        
        # 从配置获取缩放比例
        if _config_available:
            try:
                config = get_ui_config()
                self._scale_factor = config.get_scale_for_resolution(width, height)
                
                # 获取规则名称用于日志
                scaling_config = config.get_scaling_config()
                scale_name = "Unknown"
                for rule in scaling_config.rules:
                    if rule.scale == self._scale_factor:
                        scale_name = rule.name
                        break
            except Exception as e:
                logger.warning(f"从配置获取缩放比例失败: {e}，使用默认规则")
                self._scale_factor = self._calculate_scale_default(width, height)
                scale_name = self._get_scale_name_default(self._scale_factor)
        else:
            # 使用默认规则
            self._scale_factor = self._calculate_scale_default(width, height)
            scale_name = self._get_scale_name_default(self._scale_factor)
        
        logger.info(f"分辨率等级: {scale_name}, 应用缩放比例: {self._scale_factor * 100:.0f}%")
        
        return self._scale_factor
    
    def _calculate_scale_default(self, width: int, height: int) -> float:
        """
        使用默认规则计算缩放比例
        
        Args:
            width: 屏幕宽度
            height: 屏幕高度
            
        Returns:
            float: 缩放比例
        """
        if width >= 3200 or height >= 1800:
            return 2.0  # 3K 及以上
        elif width >= 2560 or height >= 1440:
            return 1.5  # 2K 分辨率
        else:
            return 1.0  # 1K 及以下
    
    def _get_scale_name_default(self, scale: float) -> str:
        """
        获取默认规则的名称
        
        Args:
            scale: 缩放比例
            
        Returns:
            str: 规则名称
        """
        scale_names = {2.0: "3K+", 1.5: "2K", 1.0: "1K"}
        return scale_names.get(scale, "Unknown")
    
    def set_scale_factor(self, scale_factor: float) -> None:
        """
        手动设置缩放比例
        
        Args:
            scale_factor: 缩放比例值，应在 0.5 到 3.0 之间
            
        Raises:
            ValueError: 当缩放比例超出有效范围时
        """
        if not 0.5 <= scale_factor <= 3.0:
            raise ValueError(f"缩放比例应在 0.5 到 3.0 之间，当前值: {scale_factor}")
        
        self._scale_factor = scale_factor
        logger.info(f"手动设置缩放比例: {scale_factor * 100:.0f}%")
    
    def get_scale_factor(self) -> float:
        """
        获取当前缩放比例
        
        Returns:
            float: 当前缩放比例
        """
        return self._scale_factor
    
    def scale(self, value: int) -> int:
        """
        根据当前缩放比例计算实际像素值
        
        Args:
            value: 基础像素值（基于 1K 分辨率设计）
            
        Returns:
            int: 缩放后的像素值
        """
        return int(value * self._scale_factor)
    
    def get_screen_info(self) -> dict:
        """
        获取屏幕信息
        
        Returns:
            dict: 包含屏幕分辨率、DPI 和缩放比例的字典
        """
        return {
            'resolution': self._screen_resolution,
            'dpi': self._screen_dpi,
            'scale_factor': self._scale_factor,
            'scale_percent': f"{self._scale_factor * 100:.0f}%"
        }


# 全局缩放管理器实例
_scaling_manager: Optional[ScalingManager] = None


def get_scaling_manager() -> ScalingManager:
    """
    获取全局缩放管理器实例
    
    Returns:
        ScalingManager: 缩放管理器单例实例
    """
    global _scaling_manager
    if _scaling_manager is None:
        _scaling_manager = ScalingManager()
    return _scaling_manager


def calculate_scale_factor(app: Optional[QApplication] = None) -> float:
    """
    便捷函数：根据屏幕分辨率计算缩放比例
    
    Args:
        app: QApplication 实例
        
    Returns:
        float: 缩放比例
    """
    return get_scaling_manager().calculate_from_screen(app)


def scale(value: int) -> int:
    """
    便捷函数：根据当前缩放比例计算实际像素值
    
    Args:
        value: 基础像素值
        
    Returns:
        int: 缩放后的像素值
    """
    return get_scaling_manager().scale(value)
