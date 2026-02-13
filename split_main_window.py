import re
import codecs

# 读取原文件
with codecs.open('src/presentation/windows/main_window.py', 'r', 'utf-8') as f:
    content = f.read()

# 提取关键部分

# 1. 提取COLORS常量
colors_match = re.search(r"(COLORS = \{[\s\S]*?\n\})", content)
if colors_match:
    colors_code = colors_match.group(1)
    print("Found COLORS constant")

# 2. 提取SQLSyntaxHighlighter类
highlighter_match = re.search(r"(class SQLSyntaxHighlighter\(QSyntaxHighlighter\):[\s\S]*?)(?=\n\nclass |\nclass MainWindow)", content)
if highlighter_match:
    highlighter_code = highlighter_match.group(1)
    print("Found SQLSyntaxHighlighter class")

# 3. 提取各个页面方法
methods_to_extract = [
    ('_create_overview_page', 'OverviewPage'),
    ('_create_sql_query_page', 'SQLQueryPage'),
    ('_create_data_download_page', 'DataDownloadPage'),
    ('_create_data_analysis_page', 'DataAnalysisPage'),
    ('_create_history_page', 'HistoryPage'),
    ('_create_settings_page', 'SettingsPage'),
]

print("Script created successfully")
