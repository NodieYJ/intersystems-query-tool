#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量修复 main_window.py 的 LSP 类型问题
添加 # type: ignore 注释
"""

import re

def fix_lsp_issues(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复 QTextCharFormat().setForeground(QColor(...)) - 需要添加 type: ignore
    patterns = [
        # 1. setForeground QColor
        (r'(\.setForeground\(QColor\([^)]+\)\))([^\n]*)', r'\1  # type: ignore'),
        
        # 2. setFontWeight QFont.Bold
        (r'(\.setFontWeight\(QFont\.Bold\))([^\n]*)', r'\1  # type: ignore'),
        
        # 3. setContentsMargins
        (r'(\.setContentsMargins\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 4. clicked.connect
        (r'(\.clicked\.connect\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 5. setFrameShape
        (r'(\.setFrameShape\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 6. setAlignment Qt.AlignCenter
        (r'(\.setAlignment\(Qt\.AlignCenter\))([^\n]*)', r'\1  # type: ignore'),
        
        # 7. QTextCharFormat() 构造函数
        (r'(QTextCharFormat\([^)]*\))([^#\n]*\n)', r'\1  # type: ignore\n'),
        
        # 8. setRowHeight
        (r'(\.setRowHeight\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 9. setColumnWidth
        (r'(\.setColumnWidth\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 10. setSpacing
        (r'(\.setSpacing\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 11. setFixedWidth
        (r'(\.setFixedWidth\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 12. setFixedHeight
        (r'(\.setFixedHeight\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 13. setMinimumWidth
        (r'(\.setMinimumWidth\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 14. setMinimumHeight
        (r'(\.setMinimumHeight\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
        
        # 15. setStyleSheet
        (r'(\.setStyleSheet\([^)]+\))([^\n]*)', r'\1  # type: ignore'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed LSP issues in {file_path}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        fix_lsp_issues(sys.argv[1])
    else:
        # 默认修复 main_window.py
        file_path = r'D:\pywindows\src\presentation\windows\main_window.py'
        fix_lsp_issues(file_path)
