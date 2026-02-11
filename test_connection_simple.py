#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单测试连接修复是否有效
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("开始简单测试连接修复")
        
        # 导入数据服务
        from src.business.services.data_service import get_data_service
        logger.info("导入数据服务成功")
        
        # 获取数据服务实例
        data_service = get_data_service()
        logger.info("获取数据服务实例成功")
        
        # 测试连接
        logger.info("执行test_connection方法")
        result = data_service.test_connection()
        logger.info(f"test_connection结果: {result}")
        
        if result:
            logger.info("连接测试成功 - 这意味着数据库服务正在运行")
        else:
            logger.info("连接测试失败 - 这是预期的，因为没有数据库服务运行")
        
        logger.info("简单测试连接修复完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(f"异常详情: {traceback.format_exc()}")
    finally:
        logger.info("测试结束")
