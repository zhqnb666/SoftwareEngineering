"""
查询面板组件
提供条目查询和筛选功能
"""

from datetime import date
from typing import List

from PySide6.QtCore import QDate, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import QueryFilters


class QueryPanel(QWidget):
    """查询筛选面板"""

    # 信号定义
    query_clicked = Signal(dict)  # 查询信号，传递筛选条件
    reset_clicked = Signal()  # 重置信号
    export_clicked = Signal()  # 导出信号
    import_clicked = Signal()  # 导入信号

    def __init__(self, parent=None):
        """初始化查询面板

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.categories: List[str] = []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("查询筛选")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 筛选条件表单
        form_layout = QFormLayout()

        # 开始日期
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setSpecialValueText("不限")
        self.start_date.setDate(QDate.currentDate().addDays(-30))  # 默认30天前
        form_layout.addRow("开始日期:", self.start_date)

        # 结束日期
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setSpecialValueText("不限")
        self.end_date.setDate(QDate.currentDate())  # 默认今天
        form_layout.addRow("结束日期:", self.end_date)

        # 类型筛选
        self.type_combo = QComboBox()
        self.type_combo.addItems(["全部", "收入", "支出"])
        form_layout.addRow("类型:", self.type_combo)

        # 分类筛选
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部")
        form_layout.addRow("分类:", self.category_combo)

        layout.addLayout(form_layout)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 查询按钮
        self.btn_query = QPushButton("查询")
        self.btn_query.setObjectName("query_btn")
        self.btn_query.clicked.connect(self._on_query)
        button_layout.addWidget(self.btn_query)

        # 重置按钮
        self.btn_reset = QPushButton("重置")
        self.btn_reset.setObjectName("reset_btn")
        self.btn_reset.clicked.connect(self._on_reset)
        button_layout.addWidget(self.btn_reset)

        # 导出CSV按钮
        self.btn_export = QPushButton("导出CSV")
        self.btn_export.setObjectName("export_btn")
        self.btn_export.clicked.connect(self._on_export)
        button_layout.addWidget(self.btn_export)

        # 导入CSV按钮
        self.btn_import = QPushButton("导入CSV")
        self.btn_import.setObjectName("import_btn")
        self.btn_import.clicked.connect(self._on_import)
        button_layout.addWidget(self.btn_import)

        layout.addLayout(button_layout)

        # 设置样式
        self.setStyleSheet(
            """
            QFormLayout QLabel {
                font-weight: bold;
                color: #333;
            }
            QDateEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                min-height: 20px;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#query_btn {
                background: #2196F3;
                color: white;
            }
            QPushButton#query_btn:hover {
                background: #1976D2;
            }
            QPushButton#reset_btn {
                background: #9E9E9E;
                color: white;
            }
            QPushButton#reset_btn:hover {
                background: #757575;
            }
            QPushButton#export_btn {
                background: #FF9800;
                color: white;
            }
            QPushButton#export_btn:hover {
                background: #F57C00;
            }
            QPushButton#import_btn {
                background: #4CAF50;
                color: white;
            }
            QPushButton#import_btn:hover {
                background: #388E3C;
            }
        """
        )

        # 设置最大高度，防止占用过多空间
        self.setMaximumHeight(200)
        layout.addStretch()

        # 设置样式
        self.setStyleSheet(
            """
            QFormLayout QLabel {
                font-weight: bold;
                color: #333;
            }
            QDateEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                min-width: 120px;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #2196F3;
                border-radius: 4px;
                background: #2196F3;
                color: white;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
            QPushButton#btn_export {
                background: #FF9800;
                border-color: #FF9800;
            }
            QPushButton#btn_export:hover {
                background: #F57C00;
            }
            QPushButton#btn_import {
                background: #4CAF50;
                border-color: #4CAF50;
            }
            QPushButton#btn_import:hover {
                background: #45a049;
            }
        """
        )

        # 设置按钮ID用于样式
        self.btn_export.setObjectName("btn_export")
        self.btn_import.setObjectName("btn_import")

    def set_categories(self, categories: List[str]):
        """设置分类列表

        Args:
            categories: 分类名称列表
        """
        self.categories = categories

        # 更新分类下拉框
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("全部")

        for category in categories:
            self.category_combo.addItem(category)

        # 尝试恢复之前的选择
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    def get_filters(self) -> QueryFilters:
        """获取查询筛选条件

        Returns:
            筛选条件对象
        """
        # 获取日期范围
        start_date = None
        end_date = None

        if self.start_date.date().isValid() and self.start_date.text() != "不限":
            start_date = self.start_date.date().toPython()

        if self.end_date.date().isValid() and self.end_date.text() != "不限":
            end_date = self.end_date.date().toPython()

        # 获取类型
        entry_type = None
        if self.type_combo.currentText() != "全部":
            entry_type = self.type_combo.currentText()

        # 获取分类
        category = None
        if self.category_combo.currentText() != "全部":
            category = self.category_combo.currentText()

        return QueryFilters(
            start_date=start_date,
            end_date=end_date,
            entry_type=entry_type,
            category=category,
        )

    def _on_query(self):
        """查询按钮点击处理"""
        filters = self.get_filters()
        self.query_clicked.emit(filters.to_dict())

    def _on_reset(self):
        """重置按钮点击处理"""
        # 重置所有筛选条件
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.end_date.setDate(QDate.currentDate())
        self.type_combo.setCurrentIndex(0)  # "全部"
        self.category_combo.setCurrentIndex(0)  # "全部"

        # 发出重置信号
        self.reset_clicked.emit()

    def _on_export(self):
        """导出按钮点击处理"""
        self.export_clicked.emit()

    def _on_import(self):
        """导入按钮点击处理"""
        self.import_clicked.emit()

    def set_date_range(self, start_date: date = None, end_date: date = None):
        """设置日期范围

        Args:
            start_date: 开始日期
            end_date: 结束日期
        """
        if start_date:
            self.start_date.setDate(
                QDate.fromString(start_date.isoformat(), "yyyy-MM-dd")
            )

        if end_date:
            self.end_date.setDate(QDate.fromString(end_date.isoformat(), "yyyy-MM-dd"))
