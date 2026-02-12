#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据服务模块
用于处理数据相关的业务逻辑
"""

import logging
import traceback
from typing import Any, Dict, List, Optional

from src.data.repositories.database_repository import getDbRepository
from src.infrastructure.config.config_manager import get_config_manager

logger = logging.getLogger(__name__)


class DataService:
    """
    数据服务类
    """

    def __init__(self):
        """
        初始化数据服务
        """
        self.db_repository = getDbRepository()
        self.config_manager = get_config_manager()

    def get_data(
        self, query: str, params: Optional[List[Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取数据

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            Optional[List[Dict[str, Any]]]: 查询结果
        """
        try:
            logger.debug("开始执行数据获取操作")
            logger.info(f"执行查询: {query}")
            if params:
                logger.debug(f"查询参数: {params}")
            logger.debug("调用数据库仓库执行查询")
            result = self.db_repository.execute_query(query, params)
            logger.debug(f"数据获取操作完成，返回结果: {result}")
            return result
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return None

    def save_data(self, query: str, params: Optional[List[Any]] = None) -> bool:
        """
        保存数据

        Args:
            query: SQL语句
            params: 查询参数

        Returns:
            bool: 执行是否成功
        """
        try:
            logger.debug("开始执行数据保存操作")
            logger.info(f"执行保存操作: {query}")
            if params:
                logger.debug(f"保存参数: {params}")
            logger.debug("调用数据库仓库执行非查询操作")
            result = self.db_repository.execute_non_query(query, params)
            logger.debug(f"数据保存操作完成，执行结果: {result}")
            return result
        except Exception as e:
            logger.error(f"保存数据失败: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return False

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            bool: 连接是否正常
        """
        try:
            logger.debug("开始执行数据库连接测试")
            logger.info("执行数据库连接测试")
            # 执行简单查询测试连接
            logger.debug("执行测试查询: SELECT 1")
            result = self.db_repository.execute_query("SELECT 1")
            logger.debug(f"测试查询结果: {result}")
            if result and len(result) > 0:
                logger.info("数据库连接测试成功")
                logger.debug("连接测试完成，状态: 成功")
                return True
            else:
                logger.error("数据库连接测试失败: 查询未返回结果")
                logger.debug("连接测试完成，状态: 失败")
                return False
        except Exception as e:
            logger.error(f"连接测试失败: {str(e)}")
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return False


# 创建全局数据服务实例
data_service = DataService()


def get_data_service() -> DataService:
    """
    获取数据服务实例

    Returns:
        DataService: 数据服务实例
    """
    return data_service
