"""
CSV导入对话框
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QPushButton, QTextEdit, QLabel,
                             QFileDialog, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QTextCursor
from typing import List, Tuple
import os


class ImportWorker(QThread):
    """导入工作线程"""
    
    # 信号定义
    validation_finished = Signal(bool, list)  # 验证完成信号
    import_finished = Signal(int, list)       # 导入完成信号
    progress_updated = Signal(str)            # 进度更新信号
    
    def __init__(self, filepath: str, profile_id: int, importer):
        """初始化工作线程
        
        Args:
            filepath: CSV文件路径
            profile_id: 目标账户ID
            importer: 数据导入器实例
        """
        super().__init__()
        self.filepath = filepath
        self.profile_id = profile_id
        self.importer = importer
        self.operation = "validate"  # "validate" 或 "import"
    
    def set_operation(self, operation: str):
        """设置操作类型
        
        Args:
            operation: "validate" 或 "import"
        """
        self.operation = operation
    
    def run(self):
        """线程执行方法"""
        try:
            if self.operation == "validate":
                self.progress_updated.emit("正在验证文件格式...")
                is_valid, errors = self.importer.validate_csv(self.filepath)
                self.validation_finished.emit(is_valid, errors)
            
            elif self.operation == "import":
                self.progress_updated.emit("正在导入数据...")
                count, errors = self.importer.import_from_csv(self.profile_id, self.filepath)
                self.import_finished.emit(count, errors)
                
        except Exception as e:
            if self.operation == "validate":
                self.validation_finished.emit(False, [f"验证过程中发生错误: {str(e)}"])
            else:
                self.import_finished.emit(0, [f"导入过程中发生错误: {str(e)}"])


class ImportDialog(QDialog):
    """CSV导入对话框"""
    
    # 添加导入成功信号
    import_success = Signal(int)  # 导入成功信号，传递导入的数量
    
    def __init__(self, parent=None, importer=None, profile_id: int = None):
        """初始化对话框
        
        Args:
            parent: 父窗口
            importer: 数据导入器实例
            profile_id: 目标账户ID
        """
        super().__init__(parent)
        self.importer = importer
        self.profile_id = profile_id
        self.worker: ImportWorker = None
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 设置窗口属性
        self.setWindowTitle("导入 CSV 数据")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("导入 CSV 数据")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 文件选择区域
        file_layout = QFormLayout()
        
        # 文件路径输入框
        path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("请选择CSV文件")
        self.file_path_edit.setReadOnly(True)
        path_layout.addWidget(self.file_path_edit)
        
        # 浏览按钮
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._on_browse)
        path_layout.addWidget(self.browse_btn)
        
        file_layout.addRow("文件路径:", path_layout)
        layout.addLayout(file_layout)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        # 下载模板按钮
        self.template_btn = QPushButton("下载模板")
        self.template_btn.clicked.connect(self._on_download_template)
        button_layout.addWidget(self.template_btn)
        
        # 验证按钮
        self.validate_btn = QPushButton("验证文件")
        self.validate_btn.clicked.connect(self._on_validate)
        self.validate_btn.setEnabled(False)
        button_layout.addWidget(self.validate_btn)
        
        # 导入按钮
        self.import_btn = QPushButton("开始导入")
        self.import_btn.clicked.connect(self._on_import)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 日志显示区域
        log_label = QLabel("操作日志:")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        close_layout.addWidget(self.close_btn)
        
        layout.addLayout(close_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #2196F3;
                border-radius: 4px;
                background: #2196F3;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:disabled {
                background: #ccc;
                border-color: #ccc;
                color: #666;
            }
            QPushButton#template_btn {
                background: #FF9800;
                border-color: #FF9800;
            }
            QPushButton#template_btn:hover {
                background: #F57C00;
            }
            QPushButton#import_btn {
                background: #4CAF50;
                border-color: #4CAF50;
            }
            QPushButton#import_btn:hover {
                background: #45a049;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: #f9f9f9;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        
        # 设置按钮ID
        self.template_btn.setObjectName("template_btn")
        self.import_btn.setObjectName("import_btn")
        
        # 连接文件路径变化信号
        self.file_path_edit.textChanged.connect(self._on_file_path_changed)
        
        self._log("请选择要导入的CSV文件")
    
    def _on_browse(self):
        """浏览文件按钮点击处理"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择CSV文件",
            "",
            "CSV文件 (*.csv);;所有文件 (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self._log(f"已选择文件: {os.path.basename(file_path)}")
    
    def _on_file_path_changed(self):
        """文件路径变化处理"""
        has_file = bool(self.file_path_edit.text().strip())
        self.validate_btn.setEnabled(has_file)
        
        # 重置导入按钮状态
        self.import_btn.setEnabled(False)
    
    def _on_download_template(self):
        """下载模板按钮点击处理"""
        if not self.importer:
            QMessageBox.warning(self, "错误", "导入器未初始化")
            return
        
        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存CSV模板",
            "记账模板.csv",
            "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                if self.importer.save_template_csv(file_path):
                    self._log("模板文件下载成功")
                    QMessageBox.information(self, "成功", f"模板文件已保存到:\n{file_path}")
                else:
                    self._log("模板文件下载失败")
                    QMessageBox.warning(self, "错误", "模板文件保存失败")
            except Exception as e:
                self._log(f"下载模板失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"下载模板失败: {str(e)}")
    
    def _on_validate(self):
        """验证文件按钮点击处理"""
        if not self.importer:
            QMessageBox.warning(self, "错误", "导入器未初始化")
            return
        
        file_path = self.file_path_edit.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", "请选择有效的CSV文件")
            return
        
        # 禁用按钮
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 显示无限进度条
        
        # 创建工作线程
        self.worker = ImportWorker(file_path, self.profile_id, self.importer)
        self.worker.set_operation("validate")
        self.worker.validation_finished.connect(self._on_validation_finished)
        self.worker.progress_updated.connect(self._log)
        self.worker.start()
    
    def _on_import(self):
        """导入按钮点击处理"""
        if not self.importer or not self.profile_id:
            QMessageBox.warning(self, "错误", "导入参数不完整")
            return
        
        file_path = self.file_path_edit.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", "请选择有效的CSV文件")
            return
        
        # 确认导入
        reply = QMessageBox.question(
            self,
            "确认导入",
            "确定要导入数据吗？\n导入后的数据将无法撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 禁用按钮
        self._set_buttons_enabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # 创建工作线程
        self.worker = ImportWorker(file_path, self.profile_id, self.importer)
        self.worker.set_operation("import")
        self.worker.import_finished.connect(self._on_import_finished)
        self.worker.progress_updated.connect(self._log)
        self.worker.start()
    
    def _on_validation_finished(self, is_valid: bool, errors: List[str]):
        """验证完成处理"""
        self.progress_bar.setVisible(False)
        self._set_buttons_enabled(True)
        
        if is_valid:
            self._log("✓ 文件验证通过，可以开始导入")
            self.import_btn.setEnabled(True)
        else:
            self._log("✗ 文件验证失败:")
            for error in errors:
                self._log(f"  - {error}")
            
            # 显示错误摘要
            QMessageBox.warning(
                self,
                "验证失败",
                f"文件验证失败，发现 {len(errors)} 个错误。\n请查看操作日志了解详情。"
            )
    
    def _on_import_finished(self, count: int, errors: List[str]):
        """导入完成处理"""
        self.progress_bar.setVisible(False)
        self._set_buttons_enabled(True)
        
        if count > 0:
            self._log(f"✓ 成功导入 {count} 条记录")
            
            if errors:
                self._log("导入过程中的警告:")
                for error in errors:
                    self._log(f"  - {error}")
            
            # 发出导入成功信号
            self.import_success.emit(count)
            
            # 显示成功消息
            message = f"成功导入 {count} 条记录"
            if errors:
                message += f"\n但有 {len(errors)} 个警告，请查看日志"
            
            QMessageBox.information(self, "导入完成", message)
        else:
            self._log("✗ 导入失败")
            for error in errors:
                self._log(f"  - {error}")
            
            QMessageBox.warning(
                self,
                "导入失败",
                f"数据导入失败。\n请查看操作日志了解详情。"
            )
    
    def _set_buttons_enabled(self, enabled: bool):
        """设置按钮启用状态"""
        self.browse_btn.setEnabled(enabled)
        self.template_btn.setEnabled(enabled)
        self.validate_btn.setEnabled(enabled and bool(self.file_path_edit.text().strip()))
        # import_btn 的状态由验证结果决定，不在这里控制
        self.close_btn.setEnabled(enabled)
    
    def _log(self, message: str):
        """添加日志信息"""
        self.log_text.append(message)
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()