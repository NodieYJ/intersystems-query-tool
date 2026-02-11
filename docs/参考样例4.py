import sys
import csv
from datetime import datetime
from PySide2.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTextEdit, QPushButton, QTableWidget,
                               QTableWidgetItem, QFileDialog, QMessageBox, QLabel,
                               QMenu, QAction, QSplitter, QStatusBar)
from PySide2.QtCore import Qt, QSettings
from PySide2.QtGui import QFont, QKeySequence
import sqlite3
import pandas as pd

class SQLQueryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_connection = None
        self.current_data = None
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("SQL查询工具 - Python 3.8.10 + PySide2")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 数据库连接区域
        db_layout = QHBoxLayout()
        self.db_path_label = QLabel("未连接数据库")
        self.db_path_label.setStyleSheet("color: gray;")
        connect_btn = QPushButton("连接数据库")
        connect_btn.clicked.connect(self.connect_database)
        disconnect_btn = QPushButton("断开连接")
        disconnect_btn.clicked.connect(self.disconnect_database)
        
        db_layout.addWidget(self.db_path_label)
        db_layout.addStretch()
        db_layout.addWidget(connect_btn)
        db_layout.addWidget(disconnect_btn)
        main_layout.addLayout(db_layout)
        
        # 使用分割器创建可调整大小的区域
        splitter = QSplitter(Qt.Vertical)
        
        # SQL输入区域
        sql_widget = QWidget()
        sql_layout = QVBoxLayout(sql_widget)
        
        sql_label = QLabel("SQL语句输入区:")
        sql_label.setFont(QFont("Arial", 10, QFont.Bold))
        sql_layout.addWidget(sql_label)
        
        self.sql_input = QTextEdit()
        self.sql_input.setPlaceholderText("输入SQL查询语句，例如：SELECT * FROM table_name")
        self.sql_input.setMinimumHeight(150)
        sql_layout.addWidget(self.sql_input)
        
        # SQL执行按钮
        sql_buttons_layout = QHBoxLayout()
        execute_btn = QPushButton("执行查询 (F5)")
        execute_btn.clicked.connect(self.execute_query)
        execute_btn.setShortcut(QKeySequence("F5"))
        execute_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        clear_btn = QPushButton("清空SQL")
        clear_btn.clicked.connect(self.clear_sql)
        
        sql_buttons_layout.addWidget(execute_btn)
        sql_buttons_layout.addWidget(clear_btn)
        sql_buttons_layout.addStretch()
        
        sql_layout.addLayout(sql_buttons_layout)
        splitter.addWidget(sql_widget)
        
        # 查询结果区域
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        
        result_label = QLabel("查询结果展示区:")
        result_label.setFont(QFont("Arial", 10, QFont.Bold))
        result_layout.addWidget(result_label)
        
        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        result_layout.addWidget(self.result_table)
        
        # 结果信息区域
        info_layout = QHBoxLayout()
        self.row_count_label = QLabel("行数: 0")
        self.column_count_label = QLabel("列数: 0")
        self.query_time_label = QLabel("查询时间: -")
        
        info_layout.addWidget(self.row_count_label)
        info_layout.addWidget(self.column_count_label)
        info_layout.addWidget(self.query_time_label)
        info_layout.addStretch()
        result_layout.addLayout(info_layout)
        
        splitter.addWidget(result_widget)
        main_layout.addWidget(splitter)
        
        # 导出按钮
        export_btn = QPushButton("导出数据")
        export_btn.clicked.connect(self.show_export_menu)
        export_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px;")
        main_layout.addWidget(export_btn)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建导出菜单
        self.export_menu = QMenu()
        self.create_export_actions()
        
    def create_export_actions(self):
        """创建导出菜单动作"""
        export_csv_action = QAction("导出为CSV文件", self)
        export_csv_action.triggered.connect(lambda: self.export_data('csv'))
        
        export_excel_action = QAction("导出为Excel文件", self)
        export_excel_action.triggered.connect(lambda: self.export_data('excel'))
        
        export_txt_action = QAction("导出为文本文件(TXT)", self)
        export_txt_action.triggered.connect(lambda: self.export_data('txt'))
        
        self.export_menu.addAction(export_csv_action)
        self.export_menu.addAction(export_excel_action)
        self.export_menu.addAction(export_txt_action)
        
    def load_settings(self):
        """加载程序设置"""
        settings = QSettings("SQLQueryApp", "Settings")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
    def save_settings(self):
        """保存程序设置"""
        settings = QSettings("SQLQueryApp", "Settings")
        settings.setValue("geometry", self.saveGeometry())
        
    def connect_database(self):
        """连接数据库"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据库文件", "", 
            "SQLite数据库 (*.db *.sqlite *.sqlite3);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self.db_connection = sqlite3.connect(file_path)
                self.db_path_label.setText(f"已连接: {file_path}")
                self.db_path_label.setStyleSheet("color: green;")
                self.status_bar.showMessage(f"成功连接到数据库：{file_path}")
                
                # 显示可用的表
                self.show_available_tables()
                
            except sqlite3.Error as e:
                QMessageBox.critical(self, "数据库连接错误", f"连接数据库失败:\n{str(e)}")
                self.db_path_label.setText("连接失败")
                self.db_path_label.setStyleSheet("color: red;")
                
    def disconnect_database(self):
        """断开数据库连接"""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
            self.db_path_label.setText("未连接数据库")
            self.db_path_label.setStyleSheet("color: gray;")
            self.clear_results()
            self.status_bar.showMessage("已断开数据库连接")
            
    def show_available_tables(self):
        """显示数据库中的可用表"""
        if not self.db_connection:
            return
            
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if tables:
                table_names = [table[0] for table in tables]
                self.status_bar.showMessage(f"数据库中的表: {', '.join(table_names)}")
                
                # 在SQL输入框中添加提示
                example_sql = f"-- 可用的表: {', '.join(table_names)}\n-- 示例: SELECT * FROM {table_names[0] if table_names else 'table_name'} LIMIT 10;"
                if not self.sql_input.toPlainText().strip():
                    self.sql_input.setText(example_sql)
            else:
                self.status_bar.showMessage("数据库中没有表")
                
        except sqlite3.Error as e:
            self.status_bar.showMessage(f"获取表信息失败: {str(e)}")
            
    def execute_query(self):
        """执行SQL查询"""
        if not self.db_connection:
            QMessageBox.warning(self, "未连接数据库", "请先连接数据库")
            return
            
        sql = self.sql_input.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "SQL为空", "请输入SQL查询语句")
            return
            
        start_time = datetime.now()
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(sql)
            
            # 获取查询结果
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description] if cursor.description else []
            
            # 存储数据供导出使用
            self.current_data = {
                'columns': column_names,
                'rows': rows
            }
            
            # 显示结果
            self.display_results(column_names, rows)
            
            # 更新信息标签
            query_time = (datetime.now() - start_time).total_seconds()
            self.query_time_label.setText(f"查询时间: {query_time:.3f}秒")
            self.row_count_label.setText(f"行数: {len(rows)}")
            self.column_count_label.setText(f"列数: {len(column_names)}")
            
            self.status_bar.showMessage(f"查询成功，返回 {len(rows)} 行，{len(column_names)} 列")
            
        except sqlite3.Error as e:
            QMessageBox.critical(self, "SQL执行错误", f"执行SQL语句时出错:\n{str(e)}")
            self.status_bar.showMessage(f"查询失败: {str(e)}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误:\n{str(e)}")
            self.status_bar.showMessage(f"错误: {str(e)}")
            
    def display_results(self, columns, rows):
        """在表格中显示查询结果"""
        self.result_table.clear()
        
        # 设置列数和列标题
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        
        # 设置行数
        self.result_table.setRowCount(len(rows))
        
        # 填充数据
        for row_idx, row in enumerate(rows):
            for col_idx, cell in enumerate(row):
                item = QTableWidgetItem(str(cell) if cell is not None else "NULL")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # 设为只读
                self.result_table.setItem(row_idx, col_idx, item)
                
        # 调整列宽
        self.result_table.resizeColumnsToContents()
        
    def clear_results(self):
        """清空查询结果"""
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.row_count_label.setText("行数: 0")
        self.column_count_label.setText("列数: 0")
        self.query_time_label.setText("查询时间: -")
        self.current_data = None
        
    def clear_sql(self):
        """清空SQL输入框"""
        self.sql_input.clear()
        
    def show_export_menu(self):
        """显示导出菜单"""
        if not self.current_data or not self.current_data['rows']:
            QMessageBox.warning(self, "无数据", "没有可导出的数据，请先执行查询")
            return
            
        # 在导出按钮下方显示菜单
        export_btn = self.sender()
        if export_btn:
            self.export_menu.exec_(export_btn.mapToGlobal(export_btn.rect().bottomLeft()))
            
    def export_data(self, format_type):
        """导出数据到指定格式"""
        if not self.current_data:
            return
            
        # 设置默认文件名
        default_name = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format_type == 'csv':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存为CSV文件", 
                f"{default_name}.csv",
                "CSV文件 (*.csv);;所有文件 (*.*)"
            )
            if file_path:
                self.export_to_csv(file_path)
                
        elif format_type == 'excel':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存为Excel文件", 
                f"{default_name}.xlsx",
                "Excel文件 (*.xlsx *.xls);;所有文件 (*.*)"
            )
            if file_path:
                self.export_to_excel(file_path)
                
        elif format_type == 'txt':
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存为文本文件", 
                f"{default_name}.txt",
                "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                self.export_to_txt(file_path)
                
    def export_to_csv(self, file_path):
        """导出为CSV文件"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # 写入列标题
                writer.writerow(self.current_data['columns'])
                
                # 写入数据行
                for row in self.current_data['rows']:
                    writer.writerow(row)
                    
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            self.status_bar.showMessage(f"数据已导出到CSV文件: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出CSV文件时出错:\n{str(e)}")
            
    def export_to_excel(self, file_path):
        """导出为Excel文件"""
        try:
            # 使用pandas创建DataFrame并导出
            import pandas as pd
            
            df = pd.DataFrame(
                self.current_data['rows'],
                columns=self.current_data['columns']
            )
            
            # 根据文件扩展名选择引擎
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False, engine='openpyxl')
            else:
                df.to_excel(file_path, index=False)
                
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            self.status_bar.showMessage(f"数据已导出到Excel文件: {file_path}")
            
        except ImportError:
            QMessageBox.warning(
                self, "缺少依赖库", 
                "导出Excel需要pandas和openpyxl库。\n"
                "请安装: pip install pandas openpyxl"
            )
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出Excel文件时出错:\n{str(e)}")
            
    def export_to_txt(self, file_path):
        """导出为文本文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                # 写入列标题
                txtfile.write("\t".join(self.current_data['columns']) + "\n")
                
                # 写入数据行
                for row in self.current_data['rows']:
                    line = "\t".join(str(cell) if cell is not None else "NULL" for cell in row)
                    txtfile.write(line + "\n")
                    
            QMessageBox.information(self, "导出成功", f"数据已成功导出到:\n{file_path}")
            self.status_bar.showMessage(f"数据已导出到文本文件: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出文本文件时出错:\n{str(e)}")
            
    def closeEvent(self, event):
        """关闭事件处理"""
        self.save_settings()
        self.disconnect_database()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SQL查询工具")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    window = SQLQueryApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
