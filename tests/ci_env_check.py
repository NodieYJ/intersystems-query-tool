#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CI 环境本地验证脚本

模拟 GitHub Actions CI 环境，检查依赖安装和测试运行
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode

def main():
    """主函数"""
    print("="*60)
    print("CI 环境本地验证")
    print("="*60)
    
    results = []
    
    # 1. 检查 Python 版本
    results.append(("Python 版本", run_command([sys.executable, "--version"], "检查 Python 版本") == 0))
    
    # 2. 列出已安装的包
    results.append(("pip list", run_command([sys.executable, "-m", "pip", "list"], "已安装的包") == 0))
    
    # 3. 检查 PySide2 是否安装
    print(f"\n{'='*60}")
    print("🔍 检查 PySide2")
    print(f"{'='*60}")
    
    result = subprocess.run(
        [sys.executable, "-c", "import PySide2; print(PySide2.__version__)"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ PySide2 已安装: {result.stdout.strip()}")
        results.append(("PySide2", True))
    else:
        print(f"❌ PySide2 未安装")
        print(f"错误: {result.stderr}")
        results.append(("PySide2", False))
    
    # 4. 尝试运行测试（跳过需要 PySide2 的测试）
    print(f"\n{'='*60}")
    print("🔍 运行不需要 PySide2 的测试")
    print(f"{'='*60}")
    
    # 只运行不导入 PySide2 的测试
    test_files = [
        "tests/unit/test_config_manager.py",
        "tests/unit/test_di_container.py",
        "tests/unit/test_driver_factory.py",
        "tests/unit/test_query_history_manager.py",
        "tests/unit/test_security_utils.py",
        "tests/unit/test_service_factory.py",
    ]
    
    success = True
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n运行测试: {test_file}")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"  ✅ 通过")
            else:
                print(f"  ❌ 失败")
                print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
                success = False
    
    results.append(("部分测试", success))
    
    # 总结
    print(f"\n{'='*60}")
    print("📊 验证结果总结")
    print(f"{'='*60}")
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(p for _, p in results)
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ 所有检查通过")
    else:
        print("⚠️ 部分检查失败，需要安装 PySide2")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
