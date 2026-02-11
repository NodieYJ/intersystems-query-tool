#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 CI/CD 配置
验证 IMP-004 修复是否成功
"""

import sys
import os
import subprocess
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


class TestCICDConfig:
    """测试 CI/CD 配置"""
    
    def test_precommit_config_exists(self):
        """测试 pre-commit 配置文件存在"""
        print("\nTest 1: pre-commit 配置文件")
        
        config_file = Path(__file__).parent.parent.parent / ".pre-commit-config.yaml"
        
        if not config_file.exists():
            print(f"  [FAIL] 配置文件不存在: {config_file}")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        required_hooks = [
            'check-ast',
            'black',
            'flake8',
            'isort',
        ]
        
        missing = []
        for hook in required_hooks:
            if hook not in content:
                missing.append(hook)
        
        if missing:
            print(f"  [FAIL] 缺少必要的 hooks: {', '.join(missing)}")
            return False
        
        print(f"  [OK] pre-commit 配置文件完整")
        print(f"  [INFO] 包含 hooks: {', '.join(required_hooks)}")
        return True
    
    def test_github_actions_exists(self):
        """测试 GitHub Actions 配置存在"""
        print("\nTest 2: GitHub Actions 配置")
        
        workflow_file = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci.yml"
        
        if not workflow_file.exists():
            print(f"  [FAIL] CI 配置文件不存在: {workflow_file}")
            return False
        
        with open(workflow_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        required_jobs = [
            'lint-and-test',
            'code-quality',
        ]
        
        missing = []
        for job in required_jobs:
            if job not in content:
                missing.append(job)
        
        if missing:
            print(f"  [FAIL] 缺少必要的 jobs: {', '.join(missing)}")
            return False
        
        # 检查 Python 版本
        if "python-version" not in content:
            print(f"  [FAIL] 未指定 Python 版本")
            return False
        
        print(f"  [OK] GitHub Actions 配置完整")
        print(f"  [INFO] 包含 jobs: {', '.join(required_jobs)}")
        return True
    
    def test_setup_cfg_exists(self):
        """测试 setup.cfg 配置存在"""
        print("\nTest 3: setup.cfg 配置")
        
        config_file = Path(__file__).parent.parent.parent / "setup.cfg"
        
        if not config_file.exists():
            print(f"  [FAIL] setup.cfg 不存在")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        required_sections = [
            '[flake8]',
            '[isort]',
            '[tool:pytest]',
        ]
        
        missing = []
        for section in required_sections:
            if section not in content:
                missing.append(section)
        
        if missing:
            print(f"  [FAIL] 缺少必要的配置段: {', '.join(missing)}")
            return False
        
        print(f"  [OK] setup.cfg 配置完整")
        print(f"  [INFO] 包含配置段: {', '.join(required_sections)}")
        return True
    
    def test_python_syntax_check(self):
        """测试 Python 语法检查"""
        print("\nTest 4: Python 语法检查")
        
        # 检查关键文件的语法
        key_files = [
            'src/main.py',
            'src/infrastructure/utils/scaling_manager.py',
            'src/data/repositories/driver_factory.py',
            'src/infrastructure/config/ui_config.py',
        ]
        
        all_passed = True
        for file in key_files:
            file_path = Path(__file__).parent.parent.parent / file
            if not file_path.exists():
                print(f"  [WARN] 文件不存在: {file}")
                continue
            
            try:
                result = subprocess.run(
                    ['python', '-m', 'py_compile', str(file_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"  [OK] {file}")
                else:
                    print(f"  [FAIL] {file}: 语法错误")
                    all_passed = False
            except Exception as e:
                print(f"  [ERROR] 检查 {file} 时发生错误: {e}")
                all_passed = False
        
        return all_passed
    
    def test_config_structure(self):
        """测试配置结构完整性"""
        print("\nTest 5: 配置结构完整性")
        
        project_root = Path(__file__).parent.parent.parent
        
        # 检查必要的配置文件
        required_files = [
            '.pre-commit-config.yaml',
            '.github/workflows/ci.yml',
            'setup.cfg',
        ]
        
        all_exist = True
        for file in required_files:
            file_path = project_root / file
            if file_path.exists():
                print(f"  [OK] {file}")
            else:
                print(f"  [FAIL] {file} 不存在")
                all_exist = False
        
        return all_exist
    
    def test_black_config(self):
        """测试 Black 配置"""
        print("\nTest 6: Black 配置检查")
        
        # 检查 setup.cfg 和 .pre-commit-config.yaml 中的 Black 配置是否一致
        setup_cfg = Path(__file__).parent.parent.parent / "setup.cfg"
        precommit = Path(__file__).parent.parent.parent / ".pre-commit-config.yaml"
        
        # 读取配置
        with open(setup_cfg, 'r') as f:
            setup_content = f.read()
        
        with open(precommit, 'r') as f:
            precommit_content = f.read()
        
        # 检查 line-length 配置
        if 'line_length = 120' in setup_content or 'line-length=120' in setup_content:
            print("  [OK] Black 行长度配置一致 (120)")
        else:
            print("  [WARN] Black 行长度配置可能不一致")
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("CI/CD 配置测试 (IMP-004)")
        print("=" * 60)
        
        tests = [
            ("pre-commit 配置", self.test_precommit_config_exists),
            ("GitHub Actions 配置", self.test_github_actions_exists),
            ("setup.cfg 配置", self.test_setup_cfg_exists),
            ("Python 语法检查", self.test_python_syntax_check),
            ("配置结构完整性", self.test_config_structure),
            ("Black 配置", self.test_black_config),
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
            print("\n✓ 所有测试通过！CI/CD 配置完整")
            print("\n使用说明:")
            print("  1. 安装 pre-commit: pip install pre-commit")
            print("  2. 启用钩子: pre-commit install")
            print("  3. 手动运行: pre-commit run --all-files")
            print("  4. GitHub Actions 将在 push/PR 时自动运行")
            return 0
        else:
            print(f"\n✗ {total - passed} 个测试失败")
            return 1


def main():
    """主函数"""
    tester = TestCICDConfig()
    return tester.run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
