#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一服务工厂测试

测试ServiceFactory的正确性和完整性
"""

import unittest
from unittest.mock import patch, MagicMock


class TestServiceFactory(unittest.TestCase):
    """ServiceFactory测试类"""

    def setUp(self):
        """测试前置条件"""
        # 导入需要测试的模块
        pass

    def test_service_factory_exists(self):
        """测试ServiceFactory类存在"""
        from src.infrastructure.utils.service_factory import ServiceFactory
        
        self.assertTrue(hasattr(ServiceFactory, 'get_config_manager'))
        self.assertTrue(hasattr(ServiceFactory, 'get_security_utils'))
        self.assertTrue(hasattr(ServiceFactory, 'get_container'))

    def test_convenience_functions_exist(self):
        """测试便捷函数存在"""
        from src.infrastructure.utils.service_factory import (
            get_config_manager_service,
            get_security_service,
            get_log_service,
            get_ui_service,
            get_container_service,
        )
        
        self.assertTrue(callable(get_config_manager_service))
        self.assertTrue(callable(get_security_service))
        self.assertTrue(callable(get_log_service))
        self.assertTrue(callable(get_ui_service))
        self.assertTrue(callable(get_container_service))

    def test_initialize_function_exists(self):
        """测试initialize_functions存在"""
        from src.infrastructure.utils.service_factory import initialize_services
        
        self.assertTrue(callable(initialize_services))

    def test_service_factory_has_all_services(self):
        """测试ServiceFactory包含所有核心服务"""
        from src.infrastructure.utils.service_factory import ServiceFactory
        
        expected_methods = [
            'get_config_manager',
            'get_container',
            'get_security_utils',
            'get_log_manager',
            'get_ui_config',
            'get_scaling_manager',
            'get_optimizer',
            'get_driver_factory',
            'get_db_repository',
            'get_query_history_manager',
            'get_data_service',
            'get_data_analysis_service',
        ]
        
        for method in expected_methods:
            self.assertTrue(
                hasattr(ServiceFactory, method),
                f"ServiceFactory 应该包含方法: {method}"
            )

    def test_backward_compatibility(self):
        """测试向后兼容函数"""
        from src.infrastructure.utils.service_factory import (
            get_config_manager,
            get_security_utils,
            get_container,
        )
        
        # 这些应该仍然可用（来自原始模块）
        self.assertTrue(callable(get_config_manager))
        self.assertTrue(callable(get_security_utils))
        self.assertTrue(callable(get_container))


class TestServiceFactoryIntegration(unittest.TestCase):
    """ServiceFactory集成测试"""

    def test_factory_returns_consistent_instances(self):
        """测试工厂返回一致的实例"""
        from src.infrastructure.utils.service_factory import ServiceFactory
        
        # 重置工厂状态
        ServiceFactory.reset()
        
        # 获取同一服务两次，应该返回同一实例
        config1 = ServiceFactory.get_config_manager()
        config2 = ServiceFactory.get_config_manager()
        
        self.assertIs(config1, config2, "同一服务的多次调用应返回同一实例")

    def test_initialized_state(self):
        """测试初始化状态"""
        from src.infrastructure.utils.service_factory import ServiceFactory
        
        # 重置后应该未初始化
        ServiceFactory.reset()
        self.assertFalse(ServiceFactory.is_initialized())
        
        # 初始化后应该已初始化
        ServiceFactory.initialize()
        self.assertTrue(ServiceFactory.is_initialized())
        
        # 清理
        ServiceFactory.reset()


# 测试入口
if __name__ == '__main__':
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    unittest.main(verbosity=2)
