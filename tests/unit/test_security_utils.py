#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
安全工具单元测试
"""

import unittest
from unittest import mock

from src.infrastructure.security.security_utils import SecurityUtils, get_security_utils, sanitize_sql_input


class TestSecurityUtils(unittest.TestCase):
    """
    安全工具测试类
    """

    def setUp(self):
        """
        测试前的设置
        """
        self.security_utils = SecurityUtils()

    def test_encrypt_password(self):
        """
        测试密码加密
        """
        # 加密密码
        password = "test-password"
        encrypted = self.security_utils.encrypt_password(password)

        # 验证加密结果格式
        self.assertIn("$", encrypted)
        salt, hashed = encrypted.split("$", 1)
        self.assertTrue(len(salt) > 0)
        self.assertTrue(len(hashed) > 0)

    def test_verify_password_correct(self):
        """
        测试验证正确的密码
        """
        # 加密密码
        password = "test-password"
        encrypted = self.security_utils.encrypt_password(password)

        # 验证正确的密码
        result = self.security_utils.verify_password(password, encrypted)
        self.assertTrue(result)

    def test_verify_password_incorrect(self):
        """
        测试验证错误的密码
        """
        # 加密密码
        password = "test-password"
        encrypted = self.security_utils.encrypt_password(password)

        # 验证错误的密码
        result = self.security_utils.verify_password("wrong-password", encrypted)
        self.assertFalse(result)

    def test_validate_input_server(self):
        """
        测试验证服务器输入
        """
        # 测试有效的服务器名
        self.assertTrue(self.security_utils.validate_input("localhost", "server"))
        self.assertTrue(self.security_utils.validate_input("test-server", "server"))
        self.assertTrue(self.security_utils.validate_input("192.168.1.1", "server"))

        # 测试无效的服务器名
        self.assertFalse(self.security_utils.validate_input("test server", "server"))
        self.assertFalse(self.security_utils.validate_input("test@server", "server"))

    def test_validate_input_port(self):
        """
        测试验证端口输入
        """
        # 测试有效的端口
        self.assertTrue(self.security_utils.validate_input("1972", "port"))
        self.assertTrue(self.security_utils.validate_input("8080", "port"))

        # 测试无效的端口
        self.assertFalse(self.security_utils.validate_input("abc", "port"))
        self.assertFalse(self.security_utils.validate_input("1972a", "port"))

    def test_validate_input_username(self):
        """
        测试验证用户名输入
        """
        # 测试有效的用户名
        self.assertTrue(self.security_utils.validate_input("testuser", "username"))
        self.assertTrue(self.security_utils.validate_input("test_user123", "username"))

        # 测试无效的用户名
        self.assertFalse(self.security_utils.validate_input("test user", "username"))
        self.assertFalse(self.security_utils.validate_input("test@user", "username"))

    def test_validate_input_password(self):
        """
        测试验证密码输入
        """
        # 测试有效的密码
        self.assertTrue(self.security_utils.validate_input("password123", "password"))
        self.assertTrue(self.security_utils.validate_input("test-password", "password"))

        # 测试无效的密码（空密码）
        self.assertFalse(self.security_utils.validate_input("", "password"))

    def test_validate_input_db_type(self):
        """
        测试验证数据库类型输入
        """
        # 测试有效的数据库类型
        self.assertTrue(self.security_utils.validate_input("IRIS", "db_type"))
        self.assertTrue(self.security_utils.validate_input("Cache", "db_type"))

        # 测试无效的数据库类型
        self.assertFalse(self.security_utils.validate_input("MySQL", "db_type"))
        self.assertFalse(self.security_utils.validate_input("", "db_type"))

    def test_sanitize_sql_input(self):
        """
        测试清理SQL输入
        """
        # 测试清理SQL输入
        test_input = "SELECT * FROM users WHERE name = 'admin' -- drop table users"
        sanitized = sanitize_sql_input(test_input)

        # 验证危险字符被移除
        self.assertNotIn("'", sanitized)
        self.assertNotIn("--", sanitized)

    def test_validate_sql_query_safe(self):
        """
        测试验证安全的SQL查询
        """
        # 测试安全的SQL查询
        safe_query = "SELECT * FROM users WHERE id = 1"
        result = self.security_utils.validate_sql_query(safe_query)
        self.assertTrue(result)

    def test_validate_sql_query_dangerous(self):
        """
        测试验证危险的SQL查询
        """
        # 测试危险的SQL查询
        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "TRUNCATE TABLE users",
            "ALTER TABLE users ADD COLUMN test INT",
            "CREATE TABLE test (id INT)",
            "INSERT INTO users (name) VALUES ('test')",
            "UPDATE users SET name = 'test'",
            "EXEC sp_executesql 'DROP TABLE users'"
        ]

        for query in dangerous_queries:
            result = self.security_utils.validate_sql_query(query)
            self.assertFalse(result, f"Query '{query}' should be considered dangerous")

    def test_generate_token(self):
        """
        测试生成令牌
        """
        # 生成令牌
        token = self.security_utils.generate_token()
        self.assertTrue(len(token) > 0)

        # 生成指定长度的令牌
        token_16 = self.security_utils.generate_token(16)
        self.assertTrue(len(token_16) >= 16)

    def test_secure_config(self):
        """
        测试安全处理配置
        """
        # 测试配置
        config = {
            "database": {
                "server": "localhost",
                "password": "plain-password"
            }
        }

        # 安全处理配置
        secured = self.security_utils.secure_config(config)

        # 验证密码被加密
        self.assertIn("$", secured["database"]["password"])
        self.assertNotEqual(secured["database"]["password"], "plain-password")

    def test_get_security_utils_singleton(self):
        """
        测试获取安全工具单例
        """
        # 获取两次安全工具
        utils1 = get_security_utils()
        utils2 = get_security_utils()

        # 验证是否是同一个实例
        self.assertIs(utils1, utils2)


if __name__ == '__main__':
    unittest.main()
