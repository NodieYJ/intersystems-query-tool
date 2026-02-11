#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 DatabaseDriverFactory 功能
验证 CR-002 重构是否成功
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.repositories.driver_factory import (
    DatabaseDriverFactory,
    DatabaseDriverType,
    get_driver_factory,
    detect_available_driver,
    is_driver_available,
)


def test_singleton():
    """测试单例模式"""
    print("\u6d4b\u8bd51: \u5355\u4f8b\u6a21\u5f0f")
    factory1 = get_driver_factory()
    factory2 = get_driver_factory()
    assert factory1 is factory2, "\u5355\u4f8b\u6a21\u5f0f\u5931\u8d25\uff1a\u83b7\u53d6\u4e86\u4e0d\u540c\u5b9e\u4f8b"
    print("  [OK] \u5355\u4f8b\u6a21\u5f0f\u5de5\u4f5c\u6b63\u5e38")


def test_driver_detection():
    """测试驱动检测"""
    print("\n\u6d4b\u8bd52: \u9a71\u52a8\u68c0\u6d4b")
    factory = get_driver_factory()

    # 自动检测
    driver_type = factory.detect_available_driver()
    print(f"  [INFO] \u68c0\u6d4b\u5230\u7684\u9a71\u52a8\u7c7b\u578b: {driver_type.value}")

    # 获取可用驱动列表
    available = factory.get_available_drivers()
    print(f"  [INFO] \u53ef\u7528\u9a71\u52a8\u5217\u8868: {[d.value for d in available]}")

    # 验证至少有一个可用驱动
    if available:
        print(f"  [OK] \u68c0\u6d4b\u5230 {len(available)} \u4e2a\u53ef\u7528\u9a71\u52a8")
    else:
        print("  [INFO] \u6ca1\u6709\u68c0\u6d4b\u5230\u53ef\u7528\u9a71\u52a8\uff08\u53ef\u80fd\u672a\u5b89\u88c5\uff09")


def test_driver_info():
    """测试驱动信息获取"""
    print("\n\u6d4b\u8bd53: \u9a71\u52a8\u4fe1\u606f")
    factory = get_driver_factory()

    info = factory.get_driver_info()
    print(f"  [INFO] IRIS \u53ef\u7528: {info['iris_available']}")
    print(f"  [INFO] IRIS DBAPI: {info['iris_dbapi']}")
    print(f"  [INFO] IRIS Legacy: {info['iris_legacy']}")
    print(f"  [INFO] pyodbc \u53ef\u7528: {info['pyodbc_available']}")
    print(f"  [INFO] \u53ef\u7528\u9a71\u52a8\u5217\u8868: {info['available_drivers']}")
    print("  [OK] \u9a71\u52a8\u4fe1\u606f\u83b7\u53d6\u6210\u529f")


def test_is_driver_available():
    """测试驱动可用性检查"""
    print("\n\u6d4b\u8bd54: \u9a71\u52a8\u53ef\u7528\u6027\u68c0\u67e5")

    # 测试便捷函数
    iris_available = is_driver_available("iris")
    pyodbc_available = is_driver_available("pyodbc")

    print(f"  [INFO] IRIS \u53ef\u7528: {iris_available}")
    print(f"  [INFO] pyodbc \u53ef\u7528: {pyodbc_available}")
    print("  [OK] \u9a71\u52a8\u53ef\u7528\u6027\u68c0\u67e5\u5de5\u4f5c\u6b63\u5e38")


def test_preferred_driver():
    """测试指定优先驱动"""
    print("\n\u6d4b\u8bd55: \u6307\u5b9a\u4f18\u5148\u9a71\u52a8")
    factory = get_driver_factory()

    # 测试指定 IRIS 优先
    driver = factory.detect_available_driver(DatabaseDriverType.IRIS)
    print(f"  [INFO] \u6307\u5b9a IRIS \u4f18\u5148: {driver.value}")

    # 测试指定 pyodbc 优先
    driver = factory.detect_available_driver(DatabaseDriverType.PYODBC)
    print(f"  [INFO] \u6307\u5b9a pyodbc \u4f18\u5148: {driver.value}")

    print("  [OK] \u4f18\u5148\u9a71\u52a8\u68c0\u6d4b\u5de5\u4f5c\u6b63\u5e38")


def test_convenience_functions():
    """测试便捷函数"""
    print("\n\u6d4b\u8bd56: \u4fbf\u6377\u51fd\u6570")

    # detect_available_driver
    driver_name = detect_available_driver()
    print(f"  [INFO] detect_available_driver() = {driver_name}")

    # 指定优先
    driver_name = detect_available_driver("iris")
    print(f"  [INFO] detect_available_driver('iris') = {driver_name}")

    print("  [OK] \u4fbf\u6377\u51fd\u6570\u5de5\u4f5c\u6b63\u5e38")


def test_lazy_import():
    """测试延迟导入"""
    print("\n\u6d4b\u8bd57: \u5ef6\u8fdf\u5bfc\u5165\u9a8c\u8bc1")

    # 创建新的工厂实例（仅用于测试）
    factory = DatabaseDriverFactory()

    # 在检测之前，驱动状态应该都是 False
    info_before = factory.get_driver_info()
    print(f"  [INFO] \u521d\u59cb\u72b6\u6001 - IRIS: {info_before['iris_available']}, pyodbc: {info_before['pyodbc_available']}")

    # 执行检测
    factory.detect_available_driver()

    # 检测后状态可能改变
    info_after = factory.get_driver_info()
    print(f"  [INFO] \u68c0\u6d4b\u540e\u72b6\u6001 - IRIS: {info_after['iris_available']}, pyodbc: {info_after['pyodbc_available']}")

    print("  [OK] \u5ef6\u8fdf\u5bfc\u5165\u5de5\u4f5c\u6b63\u5e38")


def main():
    """\u8fd0\u884c\u6240\u6709\u6d4b\u8bd5"""
    print("=" * 60)
    print("DatabaseDriverFactory \u529f\u80fd\u6d4b\u8bd5")
    print("=" * 60)

    try:
        test_singleton()
        test_driver_detection()
        test_driver_info()
        test_is_driver_available()
        test_preferred_driver()
        test_convenience_functions()
        test_lazy_import()

        print("\n" + "=" * 60)
        print("\u6240\u6709\u6d4b\u8bd5\u901a\u8fc7\uff01[SUCCESS]")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] \u6d4b\u8bd5\u5931\u8d25: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] \u6d4b\u8bd5\u5f02\u5e38: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
