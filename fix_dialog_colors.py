#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量修复对话框颜色统一性脚本

自动修复对话框文件中的硬编码颜色值
"""

import re
import sys
from pathlib import Path

# 文件列表
DIALOG_FILES = [
    'src/presentation/dialogs/data_analysis_dialog.py',
    'src/presentation/dialogs/log_dialog.py',
    'src/presentation/dialogs/query_history_dialog.py',
    'src/presentation/dialogs/sql_query_dialog.py',
]

# 颜色映射表
COLOR_MAP = {
    '#10B981': "COLORS['success']",
    '#EF4444': "COLORS['error']",
    '#64748B': "COLORS['text_secondary']",
    '#94A3B8': "COLORS['text_disabled']",
    '#1E293B': "COLORS['text_primary']",
    '#2563EB': "COLORS['primary']",
    '#2196F3': "COLORS['secondary']",  # Material Blue -> secondary
    '#4CAF50': "COLORS['success']",    # Material Green -> success
    '#f44336': "COLORS['error']",      # Material Red -> error
    '#ff9800': "COLORS['warning']",    # Material Orange -> warning
    '#FF9800': "COLORS['warning']",
    '#9C27B0': "COLORS['primary']",    # Material Purple -> primary
    'green': "COLORS['success']",
    'red': "COLORS['error']",
    'blue': "COLORS['primary']",
    'gray': "COLORS['text_secondary']",
}

# 按钮样式替换映射
BUTTON_REPLACEMENTS = [
    # (模式, 替换为)
    (r'setStyleSheet\("background-color: #2196F3; color: white; padding: [^"]*"\)', "setObjectName('btn_primary')"),
    (r'setStyleSheet\("background-color: #4CAF50; color: white; padding: [^"]*"\)', "setObjectName('btn_success')"),
    (r'setStyleSheet\("background-color: #f44336; color: white[^"]*"\)', "setObjectName('btn_danger')"),
    (r'setStyleSheet\("background-color: #ff9800; color: white[^"]*"\)', "setObjectName('btn_warning')"),
    (r'setStyleSheet\("background-color: #FF9800; color: white; padding: [^"]*"\)', "setObjectName('btn_warning')"),
    (r'setStyleSheet\("background-color: #9C27B0; color: white; padding: [^"]*"\)', "setObjectName('btn_primary')"),
]


def fix_file(filepath):
    """修复单个文件"""
    print(f"\n处理: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # 1. 添加 COLORS 导入
    if 'from src.presentation.windows.main_window import COLORS' not in content:
        # 找到最后一个导入语句的位置
        import_match = re.search(r'(from [^\n]+\n|import [^\n]+\n)(?!.*(?:from |import ))', content, re.DOTALL)
        if import_match:
            insert_pos = import_match.end()
            content = content[:insert_pos] + "from src.presentation.windows.main_window import COLORS\n" + content[insert_pos:]
            changes.append("添加 COLORS 导入")
    
    # 2. 替换按钮样式
    for pattern, replacement in BUTTON_REPLACEMENTS:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            changes.append(f"替换按钮样式: {len(matches)} 处")
    
    # 3. 替换颜色值（在 f-string 中）
    for old_color, new_color in COLOR_MAP.items():
        # 匹配 setStyleSheet("...")
        pattern = f'color: {old_color}'
        if pattern in content:
            # 替换为 f-string 格式
            content = content.replace(pattern, f'color: {{{new_color}}}')
            changes.append(f"替换颜色 {old_color} -> {new_color}")
    
    # 4. 将普通的 setStyleSheet 转换为 f-string（如果包含颜色变量）
    # 查找 setStyleSheet("color: ...") 并转换为 setStyleSheet(f"color: ...")
    def convert_to_fstring(match):
        full_match = match.group(0)
        if 'COLORS[' in full_match and not full_match.startswith('setStyleSheet(f"'):
            # 转换为 f-string
            return full_match.replace('setStyleSheet("', 'setStyleSheet(f"')
        return full_match
    
    content = re.sub(r'setStyleSheet\("[^"]*COLORS\[', convert_to_fstring, content)
    
    # 5. 保存文件
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已修复: {len(changes)} 处修改")
        for change in changes:
            print(f"   - {change}")
        return True
    else:
        print("ℹ️  无需修改")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("UI颜色统一性批量修复工具")
    print("=" * 60)
    
    fixed_count = 0
    
    for filepath in DIALOG_FILES:
        if Path(filepath).exists():
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"❌ 文件不存在: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"修复完成: {fixed_count}/{len(DIALOG_FILES)} 个文件")
    print("=" * 60)


if __name__ == '__main__':
    main()
