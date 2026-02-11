#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
循环依赖检测测试

验证DI容器能正确检测并报告循环依赖
"""

import sys
import unittest

sys.path.insert(0, 'D:\\pywindows')


# 简单循环依赖类（A <-> B）
class _CycleA:
    def __init__(self, b: '_CycleB'):
        self.b = b


class _CycleB:
    def __init__(self, a: _CycleA):
        self.a = a


# 三节点循环依赖类（A -> B -> C -> A）
class _CycleC:
    def __init__(self, a: '_CycleA3'):
        self.a = a


class _CycleA3:
    def __init__(self, b: '_CycleB3'):
        self.b = b


class _CycleB3:
    def __init__(self, c: _CycleC):
        self.c = c


# 无循环依赖类（用于测试正常情况）
class _NoCycleA:
    def __init__(self, b: '_NoCycleB'):
        self.b = b


class _NoCycleB:
    def __init__(self):
        pass


class TestCircularDependency(unittest.TestCase):
    """循环依赖测试"""

    def test_direct_circular_dependency(self):
        """测试直接循环依赖检测 - A依赖B，B依赖A"""
        from src.infrastructure.di import DIContainer

        container = DIContainer()

        container.register_transient(_CycleA, _CycleA)
        container.register_transient(_CycleB, _CycleB)

        with self.assertRaises(RuntimeError) as context:
            container.resolve(_CycleA)

        self.assertIn("循环依赖", str(context.exception))
        print(f"直接循环依赖检测成功: {context.exception}")

    def test_indirect_circular_dependency(self):
        """测试间接循环依赖检测 - A依赖B，B依赖C，C依赖A"""
        from src.infrastructure.di import DIContainer

        container = DIContainer()

        container.register_transient(_CycleA3, _CycleA3)
        container.register_transient(_CycleB3, _CycleB3)
        container.register_transient(_CycleC, _CycleC)

        with self.assertRaises(RuntimeError) as context:
            container.resolve(_CycleA3)

        self.assertIn("循环依赖", str(context.exception))
        print(f"间接循环依赖检测成功: {context.exception}")

    def test_no_circular_dependency(self):
        """测试正常依赖不报错"""
        from src.infrastructure.di import DIContainer

        container = DIContainer()

        container.register_transient(_NoCycleA, _NoCycleA)
        container.register_transient(_NoCycleB, _NoCycleB)

        a = container.resolve(_NoCycleA)
        self.assertIsNotNone(a)
        self.assertIsNotNone(a.b)


if __name__ == "__main__":
    unittest.main()
