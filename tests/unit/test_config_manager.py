#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器单元测试
"""

import json
import os
import tempfile
import unittest
from unittest import mock

from src.infrastructure.config.config_manager import ConfigManager, get_config_manager


class TestConfigManager(unittest.TestCase):
    """
    配置管理器测试类
    """

    def setUp(self):
        """
        测试前的设置
        """
        # 创建临时配置文件
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """
        测试后的清理
        """
        # 删除临时文件
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

    def test_init_without_config_file(self):
        """
        测试初始化时配置文件不存在的情况
        """
        # 确保临时文件不存在
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 验证是否使用了默认配置
        self.assertEqual(config_manager.get("database.server"), "localhost")
        self.assertEqual(config_manager.get("database.port"), 1972)
        self.assertEqual(config_manager.get("application.name"), "桌面应用程序")

    def test_init_with_invalid_config_file(self):
        """
        测试初始化时配置文件格式错误的情况
        """
        # 写入无效的JSON
        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            f.write("invalid json")

        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 验证是否使用了默认配置
        self.assertEqual(config_manager.get("database.server"), "localhost")

    def test_get_existing_config(self):
        """
        测试获取存在的配置
        """
        # 写入测试配置
        test_config = {
            "database": {
                "server": "test-server",
                "port": 1972,
                "username": "test-user"
            },
            "application": {
                "name": "Test App"
            }
        }

        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)

        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 验证是否正确读取了配置
        self.assertEqual(config_manager.get("database.server"), "test-server")
        self.assertEqual(config_manager.get("database.port"), 1972)
        self.assertEqual(config_manager.get("application.name"), "Test App")

    def test_get_nonexistent_config(self):
        """
        测试获取不存在的配置
        """
        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 验证获取不存在的配置时返回默认值
        self.assertEqual(config_manager.get("nonexistent.key"), None)
        self.assertEqual(config_manager.get("nonexistent.key", "default"), "default")

    def test_set_config(self):
        """
        测试设置配置
        """
        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 设置配置
        result = config_manager.set("database.server", "new-server")
        self.assertTrue(result)

        # 验证配置是否被正确设置
        self.assertEqual(config_manager.get("database.server"), "new-server")

    def test_set_nested_config(self):
        """
        测试设置嵌套配置
        """
        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 设置嵌套配置
        result = config_manager.set("database.connection.timeout", 30)
        self.assertTrue(result)

        # 验证配置是否被正确设置
        self.assertEqual(config_manager.get("database.connection.timeout"), 30)

    def test_save_config(self):
        """
        测试保存配置
        """
        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)

        # 设置配置
        config_manager.set("database.server", "saved-server")
        config_manager.set("application.name", "Saved App")

        # 保存配置
        result = config_manager.save()
        self.assertTrue(result)

        # 验证配置是否被正确保存
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config["database"]["server"], "saved-server")
        self.assertEqual(saved_config["application"]["name"], "Saved App")

    def test_reload_config(self):
        """
        测试重新加载配置
        """
        # 写入初始配置
        initial_config = {
            "database": {
                "server": "initial-server"
            }
        }

        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_config, f)

        # 初始化配置管理器
        config_manager = ConfigManager(self.temp_file_path)
        self.assertEqual(config_manager.get("database.server"), "initial-server")

        # 修改配置文件
        updated_config = {
            "database": {
                "server": "updated-server"
            }
        }

        with open(self.temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_config, f)

        # 重新加载配置
        result = config_manager.reload()
        self.assertTrue(result)

        # 验证配置是否被正确重新加载
        self.assertEqual(config_manager.get("database.server"), "updated-server")

    def test_get_config_manager_singleton(self):
        """
        测试获取配置管理器单例
        """
        # 获取两次配置管理器
        config_manager1 = get_config_manager()
        config_manager2 = get_config_manager()

        # 验证是否是同一个实例
        self.assertIs(config_manager1, config_manager2)


if __name__ == '__main__':
    unittest.main()
