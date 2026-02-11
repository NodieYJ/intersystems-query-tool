#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
表单设计器自由拖放功能测试
"""

import sys
from PySide2.QtWidgets import QApplication
from form_designer import FormDesignerWindow, FieldType, WidgetConfig

def main():
    """测试自由拖放功能"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 创建主窗口
    window = FormDesignerWindow()
    window.show()
    
    print("=" * 60)
    print("表单设计器 - 自由拖放功能")
    print("=" * 60)
    print()
    print("新功能说明：")
    print("1. 控件可以自由拖放到画布任意位置（不再局限于垂直布局）")
    print("2. 支持网格对齐（默认开启）")
    print("3. 支持对齐辅助线（拖动时自动显示）")
    print("4. 支持方向键微调（选中后按方向键）")
    print("5. 支持多选和框选")
    print()
    print("菜单功能：")
    print("- 视图 → 显示网格: 切换网格显示")
    print("- 视图 → 吸附到网格: 切换网格吸附")
    print("- 对齐 → 左对齐/右对齐/顶部对齐/底部对齐: 对齐选中控件")
    print()
    print("工具栏功能：")
    print("- 网格按钮: 快速切换网格显示")
    print("- 吸附按钮: 快速切换网格吸附")
    print("- 对齐按钮: 对齐选中控件")
    print()
    print("=" * 60)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
