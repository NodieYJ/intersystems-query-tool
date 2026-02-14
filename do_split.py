#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 读取原文件
with open('src/presentation/windows/main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# 找到各个方法的位置
methods = {
    '_create_overview_page': None,
    '_create_sql_query_page': None,
    '_create_data_download_page': None,
    '_create_data_analysis_page': None,
    '_create_history_page': None,
    '_create_settings_page': None,
    '_create_stat_card': None,
    '_create_activity_item': None,
    '_create_history_item': None,
}

for i, line in enumerate(lines, 1):
    for method in methods.keys():
        if f'def {method}(self' in line:
            methods[method] = i
            print(f"{method}: line {i}")

print("\nMethods found successfully")
