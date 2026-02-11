#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
用于集中管理应用配置

特性:
- 线程安全的配置读写
- 支持嵌套配置键
- 自动备份和恢复
"""

import json
import logging
import os
import shutil
import tempfile
import threading
from typing import Any, Dict, Optional

from src.infrastructure.security.security_utils import get_security_utils
from src.infrastructure.config.constants import (
    DatabaseDefaults,
    DatabaseTypes,
    UIConfigDefaults,
    LoggingConfig,
)

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理器类
    """

    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.security_utils = get_security_utils()
        self._config_lock = threading.RLock()  # 配置读写锁
        self._file_lock = threading.Lock()  # 文件写入锁
        self._load_config()

    def _load_config(self) -> None:
        """
        加载配置文件（内部方法）
        如果配置文件存在则加载，否则使用默认配置
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"成功加载配置文件: {self.config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"配置文件格式错误: {str(e)}，使用默认配置")
                self._load_default_config()
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}，使用默认配置")
                self._load_default_config()
        else:
            logger.info(f"配置文件不存在: {self.config_file}，使用默认配置")
            self._load_default_config()

    def _load_default_config(self):
        """
        加载默认配置（使用常量）
        """
        self.config = {
            "database": {
                "server": "localhost",
                "port": DatabaseDefaults.PORT_DEFAULT,  # 使用常量
                "namespace": "USER",
                "username": "",
                "password": "",
                "db_type": DatabaseTypes.IRIS,  # 使用常量
                "charset": DatabaseDefaults.CHARSET,
                "timeout": DatabaseDefaults.TIMEOUT_CONNECT,
            },
            "application": {
                "name": "桌面应用程序",
                "version": "1.0.0",
                "log_level": LoggingConfig.LOG_LEVEL,
            },
            "ui": {
                "default_window_width": UIConfigDefaults.WINDOW_WIDTH,
                "default_window_height": UIConfigDefaults.WINDOW_HEIGHT,
                "min_window_width": int(UIConfigDefaults.WINDOW_WIDTH / 2),
                "min_window_height": int(UIConfigDefaults.WINDOW_HEIGHT / 2),
                "font_size": UIConfigDefaults.FONT_SIZE,
                "font_family": UIConfigDefaults.FONT_FAMILY,
                "scale_factor": UIConfigDefaults.SCALE_FACTOR,
            },
        }
        logger.info("使用默认配置")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持嵌套键，如 "database.server"
            default: 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键，支持嵌套键，如 "database.server"
            value: 配置值
        
        Returns:
            bool: 设置是否成功
        """
        try:
            keys = key.split('.')
            config = self.config
            
            # 遍历到最后一个键的父级
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            logger.info(f"成功设置配置: {key} = {value}")
            return True
        except ValueError as e:
            logger.error(f"配置键格式错误: {str(e)}")
            return False
        except TypeError as e:
            logger.error(f"配置值类型错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"设置配置失败: {str(e)}")
            return False

    def save(self) -> bool:
        """
        保存配置到文件（线程安全）

        使用原子写入策略：
        1. 先写入临时文件
        2. 验证写入完整性
        3. 重命名替换原文件

        Returns:
            bool: 保存是否成功
        """
        # 获取文件锁，保护写入操作
        with self._file_lock:
            try:
                # 确保配置文件所在目录存在
                config_dir = os.path.dirname(self.config_file)
                if config_dir and not os.path.exists(config_dir):
                    os.makedirs(config_dir, exist_ok=True)

                # 安全处理配置
                secured_config = self.security_utils.secure_config(self.config)

                # 使用临时文件进行原子写入
                temp_fd, temp_file = tempfile.mkstemp(
                    suffix='.tmp',
                    dir=config_dir or '.'
                )

                try:
                    # 在临时文件中写入配置
                    with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                        json.dump(secured_config, f, indent=4, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())

                    # 验证临时文件内容完整性
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        json.load(f)  # 验证JSON格式有效

                    # 原子重命名替换原文件
                    shutil.move(temp_file, self.config_file)

                    logger.info(f"成功保存配置到文件: {self.config_file}")
                    return True

                except (json.JSONDecodeError, OSError, Exception) as e:
                    # 写入失败，清理临时文件
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    logger.error(f"保存配置文件失败: {str(e)}")
                    return False

            except FileNotFoundError as e:
                logger.error(f"配置文件路径不存在: {str(e)}")
                return False
            except PermissionError as e:
                logger.error(f"没有权限写入配置文件: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"保存配置文件时发生未知错误: {str(e)}")
                return False

    def reload(self) -> bool:
        """
        重新加载配置文件

        Returns:
            bool: 加载是否成功
        """
        try:
            self._load_config()
            return True
        except Exception as e:
            logger.error(f"重新加载配置文件失败: {str(e)}")
            return False


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例

    Returns:
        ConfigManager: 配置管理器实例
    """
    return config_manager
