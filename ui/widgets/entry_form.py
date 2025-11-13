"""
条目表单组件
提供添加新条目的表单界面
"""

from typing import Any, Dict

from PySide6.QtCore import QDate, Signal
from PySide6.QtGui import QDoubleValidator, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)



class EntryForm(QWidget):
    """条目添加表单"""

    # 信号定义
    entry_submitted = Signal(dict)  # 条目提交信号，传递表单数据

    def __init__(self, parent=None):
        """初始化条目表单

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.categories: Dict[str, list] = {}  # 分类数据
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("添加条目")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 表单布局
        form_layout = QFormLayout()

        # 日期选择器
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("日期:", self.date_edit)

        # 类型下拉框
        self.type_combo = QComboBox()
        self.type_combo.addItems(["支出", "收入"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("类型:", self.type_combo)

        # 金额输入框
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("请输入金额")
        # 设置数字验证器
        validator = QDoubleValidator(0.0, 999999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.amount_edit.setValidator(validator)
        form_layout.addRow("金额:", self.amount_edit)

        # 一级分类下拉框
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        form_layout.addRow("一级分类:", self.category_combo)

        # 二级分类下拉框
        self.subcategory_combo = QComboBox()
        form_layout.addRow("二级分类:", self.subcategory_combo)

        # 备注输入框
        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("选填，备注信息")
        self.note_edit.setMaximumHeight(60)
        form_layout.addRow("备注:", self.note_edit)

        layout.addLayout(form_layout)

        # 提交按钮
        self.submit_btn = QPushButton("添加条目")
        self.submit_btn.clicked.connect(self._on_submit)
        layout.addWidget(self.submit_btn)

        # 添加弹性空间
        layout.addStretch()

        # 设置样式
        self.setStyleSheet(
            """
            QFormLayout QLabel {
                font-weight: bold;
                color: #333;
            }
            QDateEdit, QComboBox, QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTextEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QPushButton {
                padding: 10px;
                border: none;
                border-radius: 4px;
                background: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """
        )

    def set_categories(self, categories: Dict[str, list]):
        """设置分类数据

        Args:
            categories: 分类字典 {一级分类: [二级分类列表]}
        """
        self.categories = categories
        self._update_categories()

    def _update_categories(self):
        """更新分类下拉框"""
        current_type = self.type_combo.currentText()

        # 清空一级分类
        self.category_combo.clear()
        self.subcategory_combo.clear()

        if not self.categories:
            return

        # 根据类型筛选分类
        if current_type == "收入":
            # 收入分类
            income_categories = ["工资", "奖金", "红包", "投资收益", "其他"]
            for category in income_categories:
                if category in self.categories:
                    self.category_combo.addItem(category)
        else:
            # 支出分类
            expense_categories = [
                "餐饮",
                "交通",
                "购物",
                "娱乐",
                "医疗",
                "教育",
                "住房",
                "其他",
            ]
            for category in expense_categories:
                if category in self.categories:
                    self.category_combo.addItem(category)

        # 更新二级分类
        if self.category_combo.count() > 0:
            self._on_category_changed(self.category_combo.currentText())

    def _on_type_changed(self, type_text: str):
        """类型变化处理"""
        self._update_categories()

    def _on_category_changed(self, category_text: str):
        """一级分类变化处理"""
        # 清空二级分类
        self.subcategory_combo.clear()

        if not category_text or category_text not in self.categories:
            return

        # 添加"（无）"选项
        self.subcategory_combo.addItem("（无）")

        # 添加二级分类选项
        subcategories = self.categories.get(category_text, [])
        for subcategory in subcategories:
            self.subcategory_combo.addItem(subcategory)

    def get_form_data(self) -> Dict[str, Any]:
        """获取表单数据

        Returns:
            表单数据字典
        """
        subcategory = self.subcategory_combo.currentText()
        if subcategory == "（无）":
            subcategory = None

        note = self.note_edit.toPlainText().strip()
        if not note:
            note = None

        return {
            "date": self.date_edit.date().toPython(),
            "type": self.type_combo.currentText(),
            "amount": (
                float(self.amount_edit.text()) if self.amount_edit.text() else 0.0
            ),
            "category": self.category_combo.currentText(),
            "subcategory": subcategory,
            "note": note,
        }

    def clear_form(self):
        """清空表单"""
        self.date_edit.setDate(QDate.currentDate())
        self.type_combo.setCurrentIndex(0)
        self.amount_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.subcategory_combo.setCurrentIndex(0)
        self.note_edit.clear()

    def _validate_form(self) -> tuple:
        """验证表单数据

        Returns:
            (是否有效, 错误消息)
        """
        # 验证金额
        amount_text = self.amount_edit.text().strip()
        if not amount_text:
            return False, "请输入金额"

        try:
            amount = float(amount_text)
            if amount <= 0:
                return False, "金额必须大于0"
        except ValueError:
            return False, "金额格式不正确"

        # 验证分类
        if not self.category_combo.currentText():
            return False, "请选择一级分类"

        return True, ""

    def _on_submit(self):
        """提交按钮点击处理"""
        # 验证表单
        is_valid, error_msg = self._validate_form()
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return

        # 获取表单数据并发出信号
        form_data = self.get_form_data()
        self.entry_submitted.emit(form_data)

        # 清空表单
        self.clear_form()
