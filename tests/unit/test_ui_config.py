#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 UIConfig 配置管理功能
验证 IMP-002 修复是否成功
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.infrastructure.config.ui_config import UIConfig, get_ui_config, ScalingRule


class TestUIConfig:
    """测试 UIConfig 配置管理"""
    
    def setup_test_config(self, config_content):
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config_content, f)
            return f.name
    
    def test_default_config_loading(self):
        """测试默认配置加载"""
        print("\nTest 1: 默认配置加载")
        
        # 使用不存在的配置文件路径，触发默认配置
        with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as tmp:
            non_existent_path = tmp.name
        
        config = UIConfig(non_existent_path)
        
        # 验证默认缩放配置
        scaling_config = config.get_scaling_config()
        assert scaling_config.default_scale == 1.0
        assert scaling_config.min_scale == 0.5
        assert scaling_config.max_scale == 3.0
        assert len(scaling_config.rules) == 3  # 3条默认规则
        
        print("  [OK] 默认缩放配置正确")
        
        # 验证默认数据库配置
        db_config = config.get_database_config()
        assert db_config.driver_priority == ["iris", "pyodbc"]
        assert db_config.connection_timeout == 30
        
        print("  [OK] 默认数据库配置正确")
    
    def test_custom_config_loading(self):
        """测试自定义配置加载"""
        print("\nTest 2: 自定义配置加载")
        
        custom_config = {
            "scaling": {
                "rules": [
                    {"min_width": 3840, "min_height": 2160, "scale": 2.5, "name": "4K", "description": "4K显示器"}
                ],
                "default_scale": 1.0,
                "min_scale": 0.5,
                "max_scale": 4.0,
                "auto_detect": False
            },
            "database": {
                "driver_priority": ["pyodbc", "iris"],
                "connection_timeout": 60
            },
            "ui": {
                "theme": "dark",
                "font_family": "Arial"
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        config_path = self.setup_test_config(custom_config)
        
        try:
            config = UIConfig(config_path)
            
            # 验证自定义缩放规则
            scaling_config = config.get_scaling_config()
            assert scaling_config.auto_detect == False
            assert scaling_config.max_scale == 4.0
            assert len(scaling_config.rules) == 1
            assert scaling_config.rules[0].name == "4K"
            assert scaling_config.rules[0].scale == 2.5
            
            print("  [OK] 自定义缩放规则正确")
            
            # 验证自定义数据库配置
            db_config = config.get_database_config()
            assert db_config.driver_priority == ["pyodbc", "iris"]
            assert db_config.connection_timeout == 60
            
            print("  [OK] 自定义数据库配置正确")
            
            # 验证UI主题配置
            ui_config = config.get_ui_theme_config()
            assert ui_config.theme == "dark"
            assert ui_config.font_family == "Arial"
            
            print("  [OK] 自定义UI配置正确")
        finally:
            os.unlink(config_path)
    
    def test_scale_for_resolution(self):
        """测试根据分辨率获取缩放比例"""
        print("\nTest 3: 分辨率缩放计算")
        
        config = UIConfig()  # 使用默认配置
        
        # 测试 4K 分辨率
        scale_4k = config.get_scale_for_resolution(3840, 2160)
        assert scale_4k == 2.0  # 3K+ 规则
        print(f"  [OK] 4K分辨率 (3840x2160): {scale_4k}x")
        
        # 测试 2K 分辨率
        scale_2k = config.get_scale_for_resolution(2560, 1440)
        assert scale_2k == 1.5  # 2K 规则
        print(f"  [OK] 2K分辨率 (2560x1440): {scale_2k}x")
        
        # 测试 1K 分辨率
        scale_1k = config.get_scale_for_resolution(1920, 1080)
        assert scale_1k == 1.0  # 1K 规则
        print(f"  [OK] 1K分辨率 (1920x1080): {scale_1k}x")
    
    def test_driver_priority(self):
        """测试驱动优先级获取"""
        print("\nTest 4: 驱动优先级")
        
        custom_config = {
            "scaling": {"rules": [], "default_scale": 1.0},
            "database": {
                "driver_priority": ["pyodbc", "iris", "unknown_driver"]
            }
        }
        
        config_path = self.setup_test_config(custom_config)
        
        try:
            config = UIConfig(config_path)
            
            from src.data.repositories.driver_factory import DatabaseDriverType
            priority = config.get_driver_priority()
            
            # 验证优先级顺序
            assert len(priority) == 2  # unknown_driver 被过滤
            assert priority[0] == DatabaseDriverType.PYODBC
            assert priority[1] == DatabaseDriverType.IRIS
            
            print("  [OK] 驱动优先级正确（过滤未知驱动）")
        finally:
            os.unlink(config_path)
    
    def test_config_reload(self):
        """测试配置热重载"""
        print("\nTest 5: 配置热重载")
        
        initial_config = {
            "scaling": {
                "rules": [{"min_width": 0, "min_height": 0, "scale": 1.0, "name": "Default"}],
                "default_scale": 1.0
            },
            "database": {"driver_priority": ["iris"]},
            "ui": {},
            "logging": {}
        }
        
        config_path = self.setup_test_config(initial_config)
        
        try:
            config = UIConfig(config_path)
            
            # 验证初始配置
            scaling_config = config.get_scaling_config()
            assert scaling_config.default_scale == 1.0
            
            # 修改配置文件
            updated_config = initial_config.copy()
            updated_config["scaling"]["default_scale"] = 1.5
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f)
            
            # 热重载
            result = config.reload_config()
            assert result == True
            
            # 验证更新后的配置
            scaling_config = config.get_scaling_config()
            assert scaling_config.default_scale == 1.5
            
            print("  [OK] 配置热重载成功")
        finally:
            os.unlink(config_path)
    
    def test_logging_config(self):
        """测试日志配置"""
        print("\nTest 6: 日志配置")
        
        config = UIConfig()  # 使用默认配置
        
        logging_config = config.get_logging_config()
        assert logging_config.level == "INFO"
        assert logging_config.max_file_size_mb == 10
        assert logging_config.backup_count == 10
        assert logging_config.console_output == True
        
        print("  [OK] 日志配置正确")
    
    def test_ui_theme_config(self):
        """测试UI主题配置"""
        print("\nTest 7: UI主题配置")
        
        config = UIConfig()  # 使用默认配置
        
        ui_config = config.get_ui_theme_config()
        assert ui_config.theme == "default"
        assert ui_config.animations_enabled == True
        assert ui_config.font_family == "Microsoft YaHei"
        assert ui_config.base_font_size == 10
        
        print("  [OK] UI主题配置正确")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("UIConfig 配置管理测试 (IMP-002)")
        print("=" * 60)
        
        tests = [
            ("默认配置加载", self.test_default_config_loading),
            ("自定义配置加载", self.test_custom_config_loading),
            ("分辨率缩放计算", self.test_scale_for_resolution),
            ("驱动优先级", self.test_driver_priority),
            ("配置热重载", self.test_config_reload),
            ("日志配置", self.test_logging_config),
            ("UI主题配置", self.test_ui_theme_config),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, True))
            except Exception as e:
                print(f"\n  [ERROR] 测试异常: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))
        
        print("\n" + "=" * 60)
        print("测试结果汇总:")
        print("=" * 60)
        
        passed = sum(1 for _, r in results if r)
        total = len(results)
        
        for name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {name}")
        
        print(f"\n总计: {passed}/{total} 通过")
        
        if passed == total:
            print("\n✓ 所有测试通过！配置外部化功能正常")
            return 0
        else:
            print(f"\n✗ {total - passed} 个测试失败")
            return 1


def main():
    """主函数"""
    tester = TestUIConfig()
    return tester.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
