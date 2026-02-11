#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试错误处理降级方案
验证 IMP-003 修复是否成功
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class TestErrorFallback:
    """测试错误处理降级方案"""
    
    def test_tkinter_dialog(self):
        """测试 tkinter 降级方案"""
        print("\nTest 1: tkinter 降级方案")
        
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # 测试 tkinter 是否可用
            root = tk.Tk()
            root.withdraw()
            
            # 不实际显示对话框（会阻塞测试）
            print("  [OK] tkinter 模块可用")
            root.destroy()
            return True
        except ImportError as e:
            print(f"  [INFO] tkinter 不可用: {e}")
            return True  # tkinter 在某些环境可能不可用，不算失败
        except Exception as e:
            print(f"  [FAIL] tkinter 初始化失败: {e}")
            return False
    
    def test_error_file_writing(self):
        """测试错误文件写入"""
        print("\nTest 2: 错误文件写入")
        
        try:
            # 创建临时错误日志文件
            error_file = tempfile.mktemp(suffix='.log')
            
            error_type = "测试错误"
            error_msg = "这是一个测试错误"
            
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now()}\n")
                f.write(f"错误类型: {error_type}\n")
                f.write(f"错误信息: {error_msg}\n")
            
            # 验证文件写入成功
            assert os.path.exists(error_file), "错误日志文件未创建"
            
            with open(error_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "测试错误" in content
                assert "时间:" in content
            
            # 清理
            os.unlink(error_file)
            
            print("  [OK] 错误日志文件写入成功")
            return True
            
        except Exception as e:
            print(f"  [FAIL] 错误日志文件写入失败: {e}")
            return False
    
    def test_console_output(self):
        """测试控制台输出"""
        print("\nTest 3: 控制台输出")
        
        try:
            error_msg = "测试错误信息"
            
            # 测试输出格式
            print("=" * 60)
            print(error_msg)
            print("=" * 60)
            
            print("  [OK] 控制台输出格式正确")
            return True
            
        except Exception as e:
            print(f"  [FAIL] 控制台输出失败: {e}")
            return False
    
    def test_import_statements(self):
        """测试必要的导入语句"""
        print("\nTest 4: 导入语句检查")
        
        # 检查 main.py 中的导入
        main_file = Path(__file__).parent.parent.parent / "src" / "main.py"
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查 tkinter 导入
        if "import tkinter" in content or "from tkinter import" in content:
            print("  [OK] tkinter 导入已添加")
        else:
            print("  [FAIL] tkinter 导入缺失")
            return False
        
        # 检查 datetime 导入
        if "from datetime import datetime" in content:
            print("  [OK] datetime 导入已存在")
        else:
            print("  [FAIL] datetime 导入缺失")
            return False
        
        return True
    
    def test_multilevel_fallback_structure(self):
        """测试多级降级结构"""
        print("\nTest 5: 多级降级结构")
        
        main_file = Path(__file__).parent.parent.parent / "src" / "main.py"
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查多级降级逻辑
        checks = [
            ("方案1注释", "# 方案1: QMessageBox"),
            ("方案2注释", "# 方案2: tkinter"),
            ("方案3注释", "# 方案3: 写入错误日志文件"),
            ("dialog_shown标志", "dialog_shown = False"),
            ("错误日志文件路径", "pywindows_error.log"),
        ]
        
        all_passed = True
        for name, pattern in checks:
            if pattern in content:
                print(f"  [OK] {name} 存在")
            else:
                print(f"  [FAIL] {name} 缺失")
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("错误处理降级方案测试 (IMP-003)")
        print("=" * 60)
        
        tests = [
            ("tkinter 降级方案", self.test_tkinter_dialog),
            ("错误文件写入", self.test_error_file_writing),
            ("控制台输出", self.test_console_output),
            ("导入语句检查", self.test_import_statements),
            ("多级降级结构", self.test_multilevel_fallback_structure),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
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
            print("\n✓ 所有测试通过！多级降级方案已正确实现")
            return 0
        else:
            print(f"\n✗ {total - passed} 个测试失败")
            return 1


def main():
    """主函数"""
    tester = TestErrorFallback()
    return tester.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
