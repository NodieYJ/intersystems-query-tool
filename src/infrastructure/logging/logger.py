#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志记录模块
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import threading

# 日志配置常量
LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB，单个日志文件最大大小
LOG_BACKUP_COUNT = 10  # 保留的备份文件数量
LOG_ENCODING = "utf-8"  # 日志文件编码


class CustomRotatingFileHandler(RotatingFileHandler):
    """
    自定义轮转文件处理器，支持按日期和轮转次数命名
    """
    
    def __init__(self, base_filename, maxBytes=0, backupCount=0, encoding="utf-8", delay=False):
        """
        初始化自定义轮转文件处理器
        
        Args:
            base_filename: 基础文件名
            maxBytes: 每个日志文件的最大大小
            backupCount: 保留的备份文件数量
            encoding: 编码格式
            delay: 是否延迟创建文件
        """
        super().__init__(base_filename, 'a', maxBytes, backupCount, encoding, delay)
        self.base_filename = base_filename
    
    def doRollover(self):
        """
        执行日志文件轮转
        """
        if self.stream:
            self.stream.close()
            self.stream = None  # type: ignore
        
        # 获取当前日期
        current_date = datetime.now().strftime("%Y%m%d")
        
        # 构建基础文件名
        base_name = os.path.splitext(self.base_filename)[0]
        ext = os.path.splitext(self.base_filename)[1]
        
        # 查找现有的备份文件，确定下一个轮转次数
        backup_count = 1
        while True:
            backup_filename = f"{base_name}_{current_date}_{backup_count}{ext}"
            if not os.path.exists(backup_filename):
                break
            backup_count += 1
        
        # 重命名当前日志文件
        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, backup_filename)
        
        # 创建新的日志文件
        if not self.delay:
            self.stream = self._open()


class LogManager:
    """
    日志管理器类，负责日志的配置和管理
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        """
        单例模式
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LogManager, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """
        初始化日志管理器
        """
        current_dir = os.path.abspath(__file__)
        src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        self.log_dir = os.path.join(src_dir, "log")
        os.makedirs(self.log_dir, exist_ok=True)

        self._setup_logger()
    
    def _setup_logger(self):
        """
        设置日志记录器
        """
        # 配置日志文件
        log_file = os.path.join(self.log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        
        # 创建自定义轮转文件处理器
        handler = CustomRotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_MAX_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding=LOG_ENCODING
        )
        
        # 设置日志级别
        handler.setLevel(logging.DEBUG)
        
        # 设置日志格式
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        
        # 获取根日志记录器
        self.logger = logging.getLogger()
        
        # 清空现有处理器
        for existing_handler in self.logger.handlers:
            self.logger.removeHandler(existing_handler)
            existing_handler.close()
        
        # 设置日志级别
        self.logger.setLevel(logging.DEBUG)
        
        # 添加处理器
        self.logger.addHandler(handler)
        
        # 记录初始化信息
        self.logger.info(f"日志管理器初始化成功，日志保存路径: {self.log_dir}")
    
    def get_logger(self):
        """
        获取日志记录器
        
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        return self.logger
    
    def shutdown(self):
        """
        关闭日志管理器
        """
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)


def setup_logger() -> logging.Logger:
    """
    设置日志记录器

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    log_manager = LogManager()
    return log_manager.get_logger()


def get_log_manager() -> LogManager:
    """
    获取日志管理器实例
    
    Returns:
        LogManager: 日志管理器实例
    """
    return LogManager()
