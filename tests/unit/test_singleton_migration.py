#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
单例迁移测试

验证所有单例都通过DI容器管理
"""

import sys
import unittest

sys.path.insert(0, 'D:\\pywindows')


class TestSingletonMigration(unittest.TestCase):
    """单例迁移测试"""

    @classmethod
    def setUpClass(cls):
        """初始化DI容器（所有测试前执行）"""
        from src.infrastructure.di.service_registration import initialize_container
        initialize_container()

    def test_security_utils_via_di(self):
        """测试SecurityUtils通过DI容器获取"""
        from src.infrastructure.di.service_registration import ISecurityUtils, get_service

        security1 = get_service(ISecurityUtils)
        security2 = get_service(ISecurityUtils)

        # DI管理的应该是同一个实例
        self.assertIs(security1, security2)

    def test_database_factory_via_di(self):
        """测试DatabaseDriverFactory通过DI容器获取"""
        from src.infrastructure.di.service_registration import IDatabaseDriverFactory, get_service

        factory1 = get_service(IDatabaseDriverFactory)
        factory2 = get_service(IDatabaseDriverFactory)

        self.assertIs(factory1, factory2)

    def test_security_utils_legacy_getter(self):
        """测试SecurityUtils传统getter"""
        from src.infrastructure.security.security_utils import get_security_utils
        from src.infrastructure.di.service_registration import ISecurityUtils, get_service

        # 旧方式和新方式应该返回同一实例
        legacy = get_security_utils()
        di_version = get_service(ISecurityUtils)

        self.assertIs(legacy, di_version)


if __name__ == "__main__":
    unittest.main()
