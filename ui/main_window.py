"""
主窗口
协调各个组件，提供统一的用户界面
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QMenuBar, QStatusBar, QMessageBox,
                             QFileDialog, QApplication)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon
from typing import Optional
import sys
import os
import logging

# 导入核心模块
from core.database import Database, get_default_db_path
from core.profile_manager import ProfileManager
from core.entry_manager import EntryManager
from core.category_manager import CategoryManager
from core.importer import DataImporter
from core.exporter import DataExporter
from core.models import Profile, QueryFilters

# 导入界面组件
from ui.widgets.profile_selector import ProfileSelector
from ui.widgets.entry_form import EntryForm
from ui.widgets.statistics_panel import StatisticsPanel
from ui.widgets.query_panel import QueryPanel
from ui.widgets.entry_table import EntryTable
from ui.dialogs.profile_dialog import ProfileDialog
from ui.dialogs.import_dialog import ImportDialog


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 数据库和管理器
        self.db: Optional[Database] = None
        self.profile_mgr: Optional[ProfileManager] = None
        self.entry_mgr: Optional[EntryManager] = None
        self.category_mgr: Optional[CategoryManager] = None
        self.importer: Optional[DataImporter] = None
        self.exporter: Optional[DataExporter] = None
        
        # 当前账户
        self.current_profile: Optional[Profile] = None
        
        # 界面组件
        self.profile_selector: Optional[ProfileSelector] = None
        self.entry_form: Optional[EntryForm] = None
        self.statistics_panel: Optional[StatisticsPanel] = None
        self.query_panel: Optional[QueryPanel] = None
        self.entry_table: Optional[EntryTable] = None
        
        # 设置状态栏定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._clear_status_message)
        
        # 初始化
        self.init_database()
        self.init_ui()
        self.connect_signals()
        self.load_initial_data()
    
    def init_database(self):
        """初始化数据库"""
        try:
            # 创建数据库连接
            db_path = get_default_db_path()
            self.db = Database(db_path)
            
            # 初始化数据库结构
            self.db.init_db()
            
            # 创建管理器
            self.profile_mgr = ProfileManager(self.db)
            self.entry_mgr = EntryManager(self.db)
            self.category_mgr = CategoryManager(self.db)
            self.importer = DataImporter(self.db, self.category_mgr)
            self.exporter = DataExporter(self.db)
            
            # 初始化默认分类
            self.category_mgr.init_default_categories()
            logging.getLogger(__name__).info("数据库初始化完成")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "数据库错误",
                f"数据库初始化失败: {str(e)}"
            )
            sys.exit(1)
    
    def init_ui(self):
        """初始化界面"""
        # 设置窗口属性
        self.setWindowTitle("个人记账本系统")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建菜单栏
        self.init_menubar()
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        main_layout.setSpacing(5)  # 设置间距
        
        # 账户选择器
        self.profile_selector = ProfileSelector()
        main_layout.addWidget(self.profile_selector)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板（添加条目 + 统计信息）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        left_layout.setSpacing(10)  # 设置间距
        
        # 添加条目表单
        self.entry_form = EntryForm()
        left_layout.addWidget(self.entry_form)
        
        # 统计信息面板
        self.statistics_panel = StatisticsPanel()
        left_layout.addWidget(self.statistics_panel)
        
        splitter.addWidget(left_widget)
        
        # 右侧面板（查询 + 列表）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        right_layout.setSpacing(5)  # 减少间距
        
        # 查询面板
        self.query_panel = QueryPanel()
        right_layout.addWidget(self.query_panel)
        
        # 条目表格
        self.entry_table = EntryTable()
        right_layout.addWidget(self.entry_table)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([350, 650])
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background: #f5f5f5;
            }
            QWidget {
                background: white;
            }
            QSplitter::handle {
                background: #ddd;
                width: 2px;
            }
            QSplitter::handle:hover {
                background: #bbb;
            }
            QMenuBar {
                background: #f8f8f8;
                border-bottom: 1px solid #ddd;
                color: #333;
                padding: 2px;
            }
            QMenuBar::item {
                background: transparent;
                color: #333;
                padding: 6px 12px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenuBar::item:selected {
                background: #e3f2fd;
                color: #1976d2;
            }
            QMenuBar::item:pressed {
                background: #bbdefb;
                color: #0d47a1;
            }
            QMenu {
                background: white;
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                background: transparent;
                color: #333;
                padding: 8px 24px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenu::item:selected {
                background: #e3f2fd;
                color: #1976d2;
            }
            QMenu::item:pressed {
                background: #bbdefb;
                color: #0d47a1;
            }
            QMenu::separator {
                height: 1px;
                background: #eee;
                margin: 4px 8px;
            }
            QCalendarWidget {
                background: white;
                border: 1px solid #ccc;
            }
            QCalendarWidget QWidget {
                background: white;
                color: #333;
            }
            QCalendarWidget QToolButton {
                background: transparent;
                color: #333;
                border: none;
                padding: 4px;
                margin: 2px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QCalendarWidget QToolButton:hover {
                background: #e3f2fd;
                color: #1976d2;
            }
            QCalendarWidget QToolButton:pressed {
                background: #bbdefb;
                color: #0d47a1;
            }
            QCalendarWidget QMenu {
                background: white;
                color: #333;
                border: 1px solid #ccc;
            }
            QCalendarWidget QSpinBox {
                background: white;
                color: #333;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px;
                font-weight: bold;
            }
            QCalendarWidget QAbstractItemView {
                background: white;
                color: #333;
                selection-background-color: #e3f2fd;
                selection-color: #1976d2;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #333;
                background: white;
            }
            QCalendarWidget QTableView {
                background: white;
                gridline-color: #eee;
            }
        """)
    
    def init_menubar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 新建账户
        new_profile_action = QAction("新建账户(&N)", self)
        new_profile_action.setShortcut("Ctrl+N")
        new_profile_action.triggered.connect(self._on_new_profile)
        file_menu.addAction(new_profile_action)
        
        file_menu.addSeparator()
        
        # 导入CSV
        import_action = QAction("导入CSV(&I)", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._on_import_csv)
        file_menu.addAction(import_action)
        
        # 导出CSV
        export_action = QAction("导出CSV(&E)", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 刷新
        refresh_action = QAction("刷新(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all)
        edit_menu.addAction(refresh_action)
        
        # 数据菜单
        data_menu = menubar.addMenu("数据(&D)")
        
        # 查询条目
        query_action = QAction("查询条目(&Q)", self)
        query_action.setShortcut("Ctrl+F")
        query_action.triggered.connect(self._on_query_entries)
        data_menu.addAction(query_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def connect_signals(self):
        """连接信号"""
        # 账户选择器信号
        self.profile_selector.profile_changed.connect(self.on_profile_changed)
        self.profile_selector.new_profile_clicked.connect(self._on_new_profile)
        self.profile_selector.delete_profile_clicked.connect(self._on_delete_profile)
        
        # 条目表单信号
        self.entry_form.entry_submitted.connect(self.on_add_entry)
        
        # 查询面板信号
        self.query_panel.query_clicked.connect(self._on_query_entries)
        self.query_panel.reset_clicked.connect(self._on_reset_query)
        self.query_panel.export_clicked.connect(self._on_export_csv)
        self.query_panel.import_clicked.connect(self._on_import_csv)
        
        # 条目表格信号
        self.entry_table.delete_clicked.connect(self.on_delete_entry)
    
    def load_initial_data(self):
        """加载初始数据"""
        # 加载账户列表
        profiles = self.profile_mgr.list_profiles()
        
        if not profiles:
            # 如果没有账户，创建默认账户
            try:
                default_profile = self.profile_mgr.create_profile("默认账本", "默认记账账户")
                profiles = [default_profile]
                self._show_status_message("已创建默认账户")
            except Exception as e:
                QMessageBox.warning(self, "警告", f"创建默认账户失败: {str(e)}")
                return
        
        # 设置账户列表
        self.profile_selector.set_profiles(profiles)
        
        # 设置当前账户（第一个）
        if profiles:
            self.on_profile_changed(profiles[0].id)
        
        # 加载分类数据
        self._load_categories()
    
    def _load_categories(self):
        """加载分类数据"""
        try:
            # 获取分类结构
            income_categories = self.category_mgr.get_categories_by_type("收入")
            expense_categories = self.category_mgr.get_categories_by_type("支出")
            
            # 合并分类
            all_categories = {**income_categories, **expense_categories}
            
            # 更新组件
            self.entry_form.set_categories(all_categories)
            
            # 获取一级分类列表用于查询面板
            primary_categories = list(all_categories.keys())
            self.query_panel.set_categories(primary_categories)
            
        except Exception as e:
            logging.getLogger(__name__).exception("加载分类失败: %s", e)
    
    def on_profile_changed(self, profile_id: int):
        """账户切换处理"""
        try:
            # 获取账户信息
            self.current_profile = self.profile_mgr.get_profile(profile_id)
            if not self.current_profile:
                QMessageBox.warning(self, "错误", "账户不存在")
                return
            
            # 更新窗口标题
            self.setWindowTitle(f"个人记账本系统 - {self.current_profile.name}")
            
            # 刷新数据
            self.refresh_entries()
            self.refresh_statistics()
            
            self._show_status_message(f"已切换到账户: {self.current_profile.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换账户失败: {str(e)}")
    
    def on_add_entry(self, entry_data: dict):
        """添加条目处理"""
        if not self.current_profile:
            QMessageBox.warning(self, "警告", "请先选择账户")
            return
        
        try:
            # 添加条目
            entry = self.entry_mgr.add_entry(
                profile_id=self.current_profile.id,
                entry_date=entry_data["date"],
                entry_type=entry_data["type"],
                amount=entry_data["amount"],
                category=entry_data["category"],
                subcategory=entry_data["subcategory"],
                note=entry_data["note"]
            )
            
            # 刷新界面
            self.refresh_entries()
            self.refresh_statistics()
            
            self._show_status_message("条目添加成功")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加条目失败: {str(e)}")
    
    def on_delete_entry(self, entry_id: int):
        """删除条目处理"""
        try:
            success = self.entry_mgr.delete_entry(entry_id)
            
            if success:
                # 刷新界面
                self.refresh_entries()
                self.refresh_statistics()
                self._show_status_message("条目删除成功")
            else:
                QMessageBox.warning(self, "警告", "删除条目失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除条目失败: {str(e)}")
    
    def refresh_entries(self):
        """刷新条目列表"""
        if not self.current_profile:
            self.entry_table.clear_table()
            return
        
        try:
            # 获取查询条件
            filters = self.query_panel.get_filters()
            
            # 获取条目列表
            entries = self.entry_mgr.get_entries(self.current_profile.id, filters)
            
            # 更新表格
            self.entry_table.set_entries(entries)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新条目列表失败: {str(e)}")
    
    def refresh_statistics(self):
        """刷新统计信息"""
        if not self.current_profile:
            self.statistics_panel.clear_statistics()
            return
        
        try:
            # 获取查询条件
            filters = self.query_panel.get_filters()
            
            # 获取统计数据
            statistics = self.entry_mgr.get_statistics(self.current_profile.id, filters)
            
            # 更新统计面板
            self.statistics_panel.update_statistics(statistics.to_dict())
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新统计信息失败: {str(e)}")
    
    def refresh_all(self):
        """刷新所有数据"""
        self.refresh_entries()
        self.refresh_statistics()
        self._show_status_message("数据已刷新")
    
    def _on_new_profile(self):
        """新建账户处理"""
        dialog = ProfileDialog(self)
        
        if dialog.exec() == ProfileDialog.Accepted:
            data = dialog.get_data()
            
            try:
                # 创建新账户
                profile = self.profile_mgr.create_profile(data["name"], data["description"])
                
                # 刷新账户列表
                profiles = self.profile_mgr.list_profiles()
                self.profile_selector.set_profiles(profiles)
                
                # 切换到新账户
                self.profile_selector.set_current_profile(profile.id)
                self.on_profile_changed(profile.id)
                
                self._show_status_message(f"账户 '{profile.name}' 创建成功")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建账户失败: {str(e)}")
    
    def _on_delete_profile(self, profile_id: int):
        """删除账户处理"""
        try:
            # 检查是否还有其他账户
            profiles = self.profile_mgr.list_profiles()
            if len(profiles) <= 1:
                QMessageBox.warning(self, "警告", "至少需要保留一个账户")
                return
            
            # 删除账户
            success = self.profile_mgr.delete_profile(profile_id)
            
            if success:
                # 刷新账户列表
                profiles = self.profile_mgr.list_profiles()
                self.profile_selector.set_profiles(profiles)
                
                # 切换到第一个账户
                if profiles:
                    self.profile_selector.set_current_profile(profiles[0].id)
                    self.on_profile_changed(profiles[0].id)
                
                self._show_status_message("账户删除成功")
            else:
                QMessageBox.warning(self, "警告", "删除账户失败")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"删除账户失败: {str(e)}")
    
    def _on_query_entries(self, filters=None):
        """查询条目处理"""
        self.refresh_entries()
        self.refresh_statistics()
        self._show_status_message("查询完成")
    
    def _on_reset_query(self):
        """重置查询处理"""
        self.refresh_entries()
        self.refresh_statistics()
        self._show_status_message("查询条件已重置")
    
    def _on_export_csv(self):
        """导出CSV处理"""
        if not self.current_profile:
            QMessageBox.warning(self, "警告", "请先选择账户")
            return
        
        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出CSV文件",
            f"{self.current_profile.name}_记账数据.csv",
            "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                # 获取当前查询条件
                filters = self.query_panel.get_filters()
                
                # 导出数据
                success = self.exporter.export_to_csv(
                    self.current_profile.id,
                    file_path,
                    filters
                )
                
                if success:
                    QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
                    self._show_status_message("CSV导出成功")
                else:
                    QMessageBox.warning(self, "警告", "导出失败，没有数据可导出")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _on_import_csv(self):
        """导入CSV处理"""
        if not self.current_profile:
            QMessageBox.warning(self, "警告", "请先选择账户")
            return
        
        dialog = ImportDialog(self, self.importer, self.current_profile.id)
        
        # 连接导入成功信号
        dialog.import_success.connect(self._on_import_success)
        
        dialog.exec()
        
        # 刷新数据（保留作为后备）
        self.refresh_entries()
        self.refresh_statistics()
    
    def _on_import_success(self, count: int):
        """导入成功处理"""
        # 立即刷新数据显示
        self.refresh_entries()
        self.refresh_statistics()
        
        # 更新状态栏
        self.status_timer.start()
        self.statusBar().showMessage(f"成功导入 {count} 条记录", 3000)
    
    def _on_about(self):
        """关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "<h3>个人记账本系统</h3>"
            "<p>版本: 1.0.0</p>"
            "<p>基于 PySide6 + SQLite 开发</p>"
            "<p>功能特色：</p>"
            "<ul>"
            "<li>多账户管理</li>"
            "<li>收支记录与分类</li>"
            "<li>数据查询与统计</li>"
            "<li>CSV 导入导出</li>"
            "</ul>"
            "<p>© 2025 个人记账本系统</p>"
        )
    
    def _show_status_message(self, message: str, timeout: int = 3000):
        """显示状态栏消息"""
        self.status_bar.showMessage(message)
        
        # 设置定时器清除消息
        self.status_timer.stop()
        if timeout > 0:
            self.status_timer.start(timeout)
    
    def _clear_status_message(self):
        """清除状态栏消息"""
        self.status_bar.showMessage("就绪")
        self.status_timer.stop()
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 关闭数据库连接
        if self.db:
            self.db.close()
        
        event.accept()