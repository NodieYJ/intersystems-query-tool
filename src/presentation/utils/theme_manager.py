#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UI主题管理器模块

提供全局QSS样式加载和管理功能。
"""

import logging
from pathlib import Path
from typing import Optional

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QTextStream

from src.infrastructure.config.app_config import get_app_config

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    UI主题管理器
    
    负责加载和管理应用程序的QSS样式。
    """
    
    _instance: Optional['ThemeManager'] = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化主题管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._current_theme = 'default'
        self._app_config = get_app_config()
        
        # 样式文件路径
        self._styles_dir = Path(__file__).parent.parent.parent.parent / 'resources' / 'styles'
        
        logger.info("ThemeManager 初始化完成")
    
    def load_stylesheet(self, filename: str = 'app.qss') -> str:
        """
        加载QSS样式文件
        
        Args:
            filename: 样式文件名
            
        Returns:
            str: QSS样式内容
        """
        stylesheet_path = self._styles_dir / filename
        
        if not stylesheet_path.exists():
            logger.warning(f"样式文件不存在: {stylesheet_path}")
            return self._get_default_stylesheet()
        
        try:
            with open(stylesheet_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                logger.info(f"成功加载样式文件: {filename}")
                return stylesheet
        except Exception as e:
            logger.error(f"加载样式文件失败: {e}")
            return self._get_default_stylesheet()
    
    def apply_stylesheet(self, app: QApplication, filename: str = 'app.qss') -> bool:
        """
        应用样式到应用程序
        
        Args:
            app: QApplication 实例
            filename: 样式文件名
            
        Returns:
            bool: 是否应用成功
        """
        try:
            stylesheet = self.load_stylesheet(filename)
            app.setStyleSheet(stylesheet)
            logger.info(f"成功应用样式: {filename}")
            return True
        except Exception as e:
            logger.error(f"应用样式失败: {e}")
            return False
    
    def reload_stylesheet(self, app: QApplication) -> bool:
        """
        重新加载并应用当前样式
        
        Args:
            app: QApplication 实例
            
        Returns:
            bool: 是否重载成功
        """
        return self.apply_stylesheet(app, f'{self._current_theme}.qss')
    
    def get_colors(self) -> dict:
        """
        获取颜色配置
        
        Returns:
            dict: 颜色配置字典
        """
        return self._app_config.get_all_colors()
    
    def get_color(self, name: str, default: str = '#000000') -> str:
        """
        获取指定颜色
        
        Args:
            name: 颜色名称
            default: 默认颜色
            
        Returns:
            str: 颜色值
        """
        return self._app_config.get_color(name, default)
    
    def _get_default_stylesheet(self) -> str:
        """
        获取默认样式（内置）
        
        Returns:
            str: 默认QSS样式
        """
        # 如果外部文件加载失败，使用这个最小化的默认样式
        return """
        /* 默认样式 */
        QMainWindow {
            background-color: #F8FAFC;
        }
        
        QPushButton {
            background-color: #2563EB;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
        }
        
        QPushButton:hover {
            background-color: #1D4ED8;
        }
        """
    
    def get_stylesheet_path(self) -> Path:
        """
        获取样式文件目录路径
        
        Returns:
            Path: 样式文件目录
        """
        return self._styles_dir
    
    def list_available_themes(self) -> list:
        """
        列出可用的主题
        
        Returns:
            list: 主题文件列表
        """
        if not self._styles_dir.exists():
            return []
        
        themes = []
        for file in self._styles_dir.glob('*.qss'):
            themes.append(file.stem)
        
        return themes


# 便捷函数
def get_theme_manager() -> ThemeManager:
    """
    获取主题管理器实例
    
    Returns:
        ThemeManager: 主题管理器单例
    """
    return ThemeManager()


def apply_app_stylesheet(app: QApplication) -> bool:
    """
    应用应用程序样式（便捷函数）
    
    Args:
        app: QApplication 实例
        
    Returns:
        bool: 是否应用成功
    """
    manager = get_theme_manager()
    return manager.apply_stylesheet(app)
