"""
条目表格组件
显示条目列表并提供操作功能
"""

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.models import Entry


class EntryTable(QWidget):
    """条目表格"""

    # 信号定义
    delete_clicked = Signal(int)  # 删除信号，传递条目ID

    def __init__(self, parent=None):
        """初始化条目表格

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.entries: List[Entry] = []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        layout.setSpacing(5)  # 设置间距

        # 标题和统计信息
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)  # 去除头部边距

        title_label = QLabel("条目列表")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 记录计数标签
        self.count_label = QLabel("共 0 条记录")
        header_layout.addWidget(self.count_label)

        layout.addLayout(header_layout)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["日期", "类型", "金额", "一级分类", "二级分类", "备注", "操作"]
        )

        # 设置表格属性
        self.table.setAlternatingRowColors(True)  # 斑马纹
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # 选择整行
        self.table.verticalHeader().setVisible(False)  # 隐藏行号
        self.table.verticalHeader().setDefaultSectionSize(36)  # 设置行高

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # 日期
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # 类型
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # 金额
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # 一级分类
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # 二级分类
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # 备注（自适应）
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # 操作

        # 设置具体列宽
        self.table.setColumnWidth(0, 90)  # 日期
        self.table.setColumnWidth(1, 50)  # 类型
        self.table.setColumnWidth(2, 90)  # 金额
        self.table.setColumnWidth(3, 70)  # 一级分类
        self.table.setColumnWidth(4, 70)  # 二级分类
        self.table.setColumnWidth(6, 100)  # 操作（增加宽度）

        layout.addWidget(self.table)

        # 设置样式
        self.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background: #e3f2fd;
            }
            QHeaderView::section {
                background: #f5f5f5;
                padding: 8px;
                border: none;
                border-right: 1px solid #ddd;
                font-weight: bold;
                color: #333;
            }
            QPushButton {
                padding: 2px 8px;
                border: 1px solid #f44336;
                border-radius: 3px;
                background: #f44336;
                color: white;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
        """
        )

    def set_entries(self, entries: List[Entry]):
        """设置条目列表

        Args:
            entries: 条目列表
        """
        self.entries = entries
        self._update_table()
        self._update_count_label()

    def _update_table(self):
        """更新表格内容"""
        self.table.setRowCount(len(self.entries))

        for row, entry in enumerate(self.entries):
            # 日期
            date_item = QTableWidgetItem(entry.date.strftime("%Y-%m-%d"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, date_item)

            # 类型
            type_item = QTableWidgetItem(entry.type)
            type_item.setTextAlignment(Qt.AlignCenter)
            # 设置类型颜色
            if entry.type == "收入":
                type_item.setForeground(QColor("#4CAF50"))
            else:
                type_item.setForeground(QColor("#F44336"))
            self.table.setItem(row, 1, type_item)

            # 金额
            amount_item = QTableWidgetItem(f"{entry.amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # 设置金额颜色
            if entry.type == "收入":
                amount_item.setForeground(QColor("#4CAF50"))
            else:
                amount_item.setForeground(QColor("#F44336"))
            self.table.setItem(row, 2, amount_item)

            # 一级分类
            category_item = QTableWidgetItem(entry.category)
            self.table.setItem(row, 3, category_item)

            # 二级分类
            subcategory_item = QTableWidgetItem(entry.subcategory or "")
            self.table.setItem(row, 4, subcategory_item)

            # 备注
            note_item = QTableWidgetItem(entry.note or "")
            self.table.setItem(row, 5, note_item)

            # 操作按钮
            delete_btn = QPushButton("删除")
            # delete_btn.setFixedSize(60, 22)  # 设置合适的按钮尺寸
            delete_btn.clicked.connect(
                lambda checked, eid=entry.id: self._on_delete(eid)
            )
            self.table.setCellWidget(row, 6, delete_btn)

    def _update_count_label(self):
        """更新记录计数标签"""
        count = len(self.entries)
        self.count_label.setText(f"共 {count} 条记录")

    def clear_table(self):
        """清空表格"""
        self.table.setRowCount(0)
        self.entries.clear()
        self._update_count_label()

    def _on_delete(self, entry_id: int):
        """删除按钮点击处理

        Args:
            entry_id: 条目ID
        """
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这条记录吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.delete_clicked.emit(entry_id)

    def refresh(self):
        """刷新表格"""
        self._update_table()
        self._update_count_label()
