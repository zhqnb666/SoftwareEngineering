"""
新建账户对话框
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QTextEdit, QPushButton, QHBoxLayout, QLabel,
                             QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from typing import Dict, Optional


class ProfileDialog(QDialog):
    """新建账户对话框"""
    
    def __init__(self, parent=None, profile_data: Dict = None):
        """初始化对话框
        
        Args:
            parent: 父窗口
            profile_data: 编辑时的账户数据（可选）
        """
        super().__init__(parent)
        self.profile_data = profile_data
        self.is_edit_mode = profile_data is not None
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 设置窗口属性
        title = "编辑账户" if self.is_edit_mode else "新建账户"
        self.setWindowTitle(title)
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 表单
        form_layout = QFormLayout()
        
        # 账户名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入账户名称（必填）")
        self.name_edit.setMaxLength(20)
        form_layout.addRow("账户名称:", self.name_edit)
        
        # 账户描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("请输入账户描述（可选）")
        self.desc_edit.setMaximumHeight(80)
        form_layout.addRow("账户描述:", self.desc_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # 确定按钮
        ok_text = "保存" if self.is_edit_mode else "创建"
        self.ok_btn = QPushButton(ok_text)
        self.ok_btn.clicked.connect(self._on_ok)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
        # 如果是编辑模式，填充现有数据
        if self.is_edit_mode and self.profile_data:
            self.name_edit.setText(self.profile_data.get('name', ''))
            self.desc_edit.setPlainText(self.profile_data.get('description', ''))
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
            QLabel {
                color: #333;
                margin: 10px 0;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                padding: 8px 20px;
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
            QPushButton#cancel_btn {
                background: #f5f5f5;
                color: #333;
                border-color: #ddd;
            }
            QPushButton#cancel_btn:hover {
                background: #e0e0e0;
            }
        """)
        
        # 设置按钮ID
        self.cancel_btn.setObjectName("cancel_btn")
        
        # 设置焦点
        self.name_edit.setFocus()
    
    def get_data(self) -> Dict[str, str]:
        """获取表单数据
        
        Returns:
            表单数据字典
        """
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip()
        }
    
    def _validate_form(self) -> tuple:
        """验证表单数据
        
        Returns:
            (是否有效, 错误消息)
        """
        name = self.name_edit.text().strip()
        
        if not name:
            return False, "账户名称不能为空"
        
        if len(name) > 20:
            return False, "账户名称不能超过20个字符"
        
        description = self.desc_edit.toPlainText().strip()
        if len(description) > 100:
            return False, "账户描述不能超过100个字符"
        
        return True, ""
    
    def _on_ok(self):
        """确定按钮点击处理"""
        # 验证表单
        is_valid, error_msg = self._validate_form()
        if not is_valid:
            QMessageBox.warning(self, "输入错误", error_msg)
            return
        
        # 关闭对话框并返回成功
        self.accept()