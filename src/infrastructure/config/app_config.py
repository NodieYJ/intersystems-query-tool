#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
应用程序配置模块

提供外部化的应用程序配置，支持YAML格式。
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class AppConfig:
    """
    应用程序配置类
    
    加载和管理外部化的应用程序配置。
    """
    
    _instance = None
    _config = None
    
    # 默认配置
    DEFAULT_CONFIG = {
        'ui': {
            'colors': {
                'primary': '#2563EB',
                'primary_hover': '#1D4ED8',
                'primary_light': '#DBEAFE',
                'secondary': '#3B82F6',
                'success': '#10B981',
                'warning': '#F59E0B',
                'error': '#EF4444',
                'info': '#3B82F6',
                'background': '#F8FAFC',
                'surface': '#FFFFFF',
                'border': '#E2E8F0',
                'divider': '#F1F5F9',
                'text_primary': '#1E293B',
                'text_secondary': '#64748B',
                'text_disabled': '#94A3B8',
                'text_inverse': '#FFFFFF',
            },
            'scaling': {
                'enabled': True,
                'base_width': 1920,
                'factors': {
                    '1k': 1.0,
                    '2k': 1.5,
                    '3k': 2.0
                }
            },
            'fonts': {
                'family': 'Microsoft YaHei, Segoe UI, sans-serif',
                'sizes': {
                    'small': 12,
                    'normal': 14,
                    'large': 16,
                    'title': 20,
                    'header': 24
                }
            }
        },
        'database': {
            'pool': {
                'max_connections': 10,
                'timeout': 30,
                'query_timeout': 30,
                'acquire_timeout': 5.0,
                'max_lifetime': 3600
            },
            'retry': {
                'max_retries': 3,
                'delay': 1.0
            }
        },
        'security': {
            'password': {
                'algorithm': 'PBKDF2HMAC',
                'iterations': 100000,
                'salt_length': 16,
                'hash_algorithm': 'SHA256'
            },
            'query': {
                'require_params': True,
                'max_query_length': 10000,
                'forbidden_keywords': [
                    'DROP', 'DELETE FROM', 'TRUNCATE', 'ALTER',
                    'CREATE', 'INSERT INTO', 'UPDATE', 'EXEC',
                    'xp_', 'sp_'
                ]
            },
            'rate_limit': {
                'enabled': True,
                'max_requests': 100,
                'window': 60
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'max_size': 10485760,  # 10MB
            'backup_count': 5
        }
    }
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if self._config is None:
            self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        config_path = self._get_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}，使用默认配置")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            # 创建默认配置文件
            self._config = self.DEFAULT_CONFIG.copy()
            self._save_default_config(config_path)
    
    def _get_config_path(self) -> Path:
        """
        获取配置文件路径
        
        Returns:
            Path: 配置文件路径
        """
        # 优先从环境变量获取
        env_path = os.environ.get('APP_CONFIG_PATH')
        if env_path:
            return Path(env_path)
        
        # 默认路径：项目根目录下的 config/app.yaml
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        return base_dir / 'config' / 'app.yaml'
    
    def _save_default_config(self, path: Path):
        """
        保存默认配置到文件
        
        Args:
            path: 配置文件路径
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存默认配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的键）
        
        Args:
            key: 配置键（如 'ui.colors.primary'）
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_color(self, name: str, default: str = '#000000') -> str:
        """
        获取颜色配置
        
        Args:
            name: 颜色名称
            default: 默认颜色
            
        Returns:
            str: 颜色值
        """
        return self.get(f'ui.colors.{name}', default)
    
    def get_db_pool_config(self) -> Dict[str, Any]:
        """
        获取数据库连接池配置
        
        Returns:
            Dict[str, Any]: 连接池配置
        """
        return self.get('database.pool', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        获取安全配置
        
        Returns:
            Dict[str, Any]: 安全配置
        """
        return self.get('security', {})
    
    def get_all_colors(self) -> Dict[str, str]:
        """
        获取所有颜色配置
        
        Returns:
            Dict[str, str]: 颜色配置字典
        """
        return self.get('ui.colors', {})
    
    def reload(self):
        """重新加载配置"""
        self._load_config()
    
    def save(self, path: Optional[str] = None):
        """
        保存当前配置到文件
        
        Args:
            path: 配置文件路径，默认为默认路径
        """
        save_path = Path(path) if path else self._get_config_path()
        
        try:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置文件失败: {e}")


# 全局配置实例
_app_config = None


def get_app_config() -> AppConfig:
    """
    获取应用程序配置实例
    
    Returns:
        AppConfig: 配置实例
    """
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config
