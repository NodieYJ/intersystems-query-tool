#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 ScalingManager 功能
验证 CR-001 重构是否成功
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.utils.scaling_manager import (
    ScalingManager,
    get_scaling_manager,
    scale,
)


def test_singleton():
    """测试单例模式"""
    print("测试1: 单例模式")
    manager1 = get_scaling_manager()
    manager2 = get_scaling_manager()
    assert manager1 is manager2, "单例模式失败：获取了不同实例"
    print("  [OK] 单例模式工作正常")


def test_scale_factor():
    """测试缩放比例设置和获取"""
    print("\n测试2: 缩放比例设置")
    manager = get_scaling_manager()
    
    # 测试设置不同的缩放比例
    test_values = [1.0, 1.5, 2.0, 0.8, 2.5]
    for value in test_values:
        manager.set_scale_factor(value)
        assert manager.get_scale_factor() == value, f"设置缩放比例失败: {value}"
        print(f"  [OK] 设置缩放比例 {value}x 成功")


def test_scale_calculation():
    """测试缩放计算"""
    print("\n测试3: 缩放计算")
    manager = get_scaling_manager()
    manager.set_scale_factor(1.5)
    
    test_cases = [
        (100, 150),
        (200, 300),
        (50, 75),
        (0, 0),
    ]
    
    for input_val, expected in test_cases:
        result = manager.scale(input_val)
        assert result == expected, f"缩放计算错误: {input_val} * 1.5 = {result}, 期望 {expected}"
        print(f"  [OK] {input_val} * 1.5 = {result}")


def test_global_scale_function():
    """测试全局便捷函数"""
    print("\n测试4: 全局便捷函数")
    manager = get_scaling_manager()
    manager.set_scale_factor(2.0)
    
    result = scale(100)
    assert result == 200, f"全局 scale 函数错误: {result}"
    print(f"  [OK] scale(100) = {result} (2.0x)")


def test_invalid_scale_factor():
    """测试无效的缩放比例"""
    print("\n测试5: 无效缩放比例检测")
    manager = get_scaling_manager()
    
    invalid_values = [0.1, 5.0, -1.0, 0.0]
    for value in invalid_values:
        try:
            manager.set_scale_factor(value)
            print(f"  [FAIL] 应该抛出异常但没有: {value}")
        except ValueError as e:
            print(f"  [OK] 正确检测到无效值 {value}: {e}")


def test_screen_info():
    """测试屏幕信息获取"""
    print("\n测试6: 屏幕信息")
    manager = get_scaling_manager()
    info = manager.get_screen_info()
    
    assert 'resolution' in info
    assert 'dpi' in info
    assert 'scale_factor' in info
    assert 'scale_percent' in info
    
    print(f"  [OK] 屏幕信息:")
    print(f"      分辨率: {info['resolution']}")
    print(f"      DPI: {info['dpi']}")
    print(f"      缩放比例: {info['scale_factor']} ({info['scale_percent']})")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("ScalingManager 功能测试")
    print("=" * 60)
    
    try:
        test_singleton()
        test_scale_factor()
        test_scale_calculation()
        test_global_scale_function()
        test_invalid_scale_factor()
        test_screen_info()
        
        print("\n" + "=" * 60)
        print("所有测试通过！[SUCCESS]")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
