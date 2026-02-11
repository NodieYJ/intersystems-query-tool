#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码覆盖率检查脚本

使用 unittest 的 coverage 替代方案
"""

import sys
import os
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.abspath('.'))

def run_coverage_check():
    """
    运行覆盖率检查
    
    返回: (total_tests, passed_tests, coverage_percent)
    """
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    suite = loader.discover('tests/unit', pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # 计算测试统计
    total_tests = result.testsRun
    passed_tests = total_tests - len(result.failures) - len(result.errors)
    
    # 估算覆盖率（基于测试文件数）
    test_files = list(Path('tests/unit').glob('test_*.py'))
    source_files = list(Path('src').glob('**/*.py'))
    
    # 简单的覆盖率估算
    tested_files = set()
    for tf in test_files:
        # 提取测试的模块名
        module_name = tf.stem.replace('test_', '')
        for sf in source_files:
            if module_name in sf.stem:
                tested_files.add(sf)
    
    total_source = len(source_files)
    tested_count = len(tested_files)
    
    # 计算覆盖率百分比
    coverage = (tested_count / total_source * 100) if total_source > 0 else 0
    
    return total_tests, passed_tests, coverage

def main():
    """主函数"""
    print("=" * 60)
    print("代码覆盖率检查")
    print("=" * 60)
    
    try:
        total, passed, coverage = run_coverage_check()
        
        print(f"\n测试统计:")
        print(f"  总测试数: {total}")
        print(f"  通过: {passed}")
        print(f"  失败: {total - passed}")
        
        print(f"\n覆盖率估算:")
        print(f"  估算覆盖率: {coverage:.1f}%")
        
        print("\n" + "=" * 60)
        
        # 检查是否达到80%阈值
        if coverage >= 80:
            print(f"✅ 覆盖率达标 ({coverage:.1f}% >= 80%)")
            return 0
        else:
            print(f"⚠️ 覆盖率未达标 ({coverage:.1f}% < 80%)")
            print("建议:")
            print("  1. 添加更多单元测试")
            print("  2. 使用 pytest-cov 生成详细报告")
            return 1
            
    except Exception as e:
        print(f"❌ 覆盖率检查失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
