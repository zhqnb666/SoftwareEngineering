"""
账户选择器组件
提供账户选择和管理功能
"""

from typing import List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

from core.models import Profile


class ProfileSelector(QWidget):
    """账户选择器"""

    # 信号定义
    profile_changed = Signal(int)  # 账户切换信号，传递账户ID
    new_profile_clicked = Signal()  # 新建账户信号
    delete_profile_clicked = Signal(int)  # 删除账户信号，传递账户ID

    def __init__(self, parent=None):
        """初始化账户选择器

        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.profiles: List[Profile] = []
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 账户标签
        self.label = QLabel("当前账户:")
        layout.addWidget(self.label)

        # 账户下拉框
        self.combo = QComboBox()
        self.combo.setMinimumWidth(150)
        self.combo.setMaximumWidth(200)
        self.combo.currentIndexChanged.connect(self._on_profile_changed)
        layout.addWidget(self.combo)

        # 新建账户按钮
        self.btn_new = QPushButton("新建账户")
        self.btn_new.clicked.connect(self._on_new_profile)
        layout.addWidget(self.btn_new)

        # 删除账户按钮
        self.btn_delete = QPushButton("删除账户")
        self.btn_delete.clicked.connect(self._on_delete_profile)
        layout.addWidget(self.btn_delete)

        # 添加弹性空间
        layout.addStretch()

        # 设置样式
        self.setStyleSheet(
            """
            QComboBox {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: white;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #2196F3;
                border-radius: 4px;
                background: #2196F3;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:pressed {
                background: #1565C0;
            }
        """
        )

    def set_profiles(self, profiles: List[Profile]):
        """设置账户列表

        Args:
            profiles: 账户列表
        """
        self.profiles = profiles

        # 清空下拉框
        self.combo.clear()

        # 添加账户选项
        for profile in profiles:
            display_text = f"{profile.name}"
            if profile.description:
                display_text += f" ({profile.description})"
            self.combo.addItem(display_text, profile.id)

        # 更新按钮状态
        self._update_button_states()

    def get_current_profile_id(self) -> Optional[int]:
        """获取当前选中的账户ID

        Returns:
            账户ID或None
        """
        current_index = self.combo.currentIndex()
        if current_index >= 0:
            return self.combo.itemData(current_index)
        return None

    def get_current_profile(self) -> Optional[Profile]:
        """获取当前选中的账户对象

        Returns:
            账户对象或None
        """
        profile_id = self.get_current_profile_id()
        if profile_id:
            for profile in self.profiles:
                if profile.id == profile_id:
                    return profile
        return None

    def set_current_profile(self, profile_id: int):
        """设置当前选中的账户

        Args:
            profile_id: 账户ID
        """
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == profile_id:
                self.combo.setCurrentIndex(i)
                break

    def _on_profile_changed(self, index: int):
        """账户选择变化处理"""
        if index >= 0:
            profile_id = self.combo.itemData(index)
            if profile_id:
                self.profile_changed.emit(profile_id)

        self._update_button_states()

    def _on_new_profile(self):
        """新建账户按钮点击处理"""
        self.new_profile_clicked.emit()

    def _on_delete_profile(self):
        """删除账户按钮点击处理"""
        current_profile = self.get_current_profile()
        if not current_profile:
            return

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除账户 '{current_profile.name}' 吗？\n"
            f"删除账户将同时删除该账户下的所有条目记录！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.delete_profile_clicked.emit(current_profile.id)

    def _update_button_states(self):
        """更新按钮状态"""
        has_profiles = self.combo.count() > 0
        has_current = self.get_current_profile_id() is not None

        # 只有当存在账户且有选中账户时，删除按钮才可用
        self.btn_delete.setEnabled(has_profiles and has_current)

        # 如果没有任何账户，禁用删除按钮
        if not has_profiles:
            self.btn_delete.setEnabled(False)

    def refresh(self):
        """刷新组件状态"""
        self._update_button_states()
