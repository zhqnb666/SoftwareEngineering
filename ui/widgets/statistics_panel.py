"""
统计信息面板组件
显示收支统计数据
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from typing import Dict, Any

from core.models import Statistics


class StatisticsPanel(QWidget):
    """统计信息面板"""
    
    def __init__(self, parent=None):
        """初始化统计面板
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("统计信息")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 统计数据容器
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Box)
        stats_layout = QVBoxLayout(stats_frame)
        
        # 总收入
        self.lbl_income = QLabel("总收入: ¥ 0.00")
        self.lbl_income.setAlignment(Qt.AlignLeft)
        stats_layout.addWidget(self.lbl_income)
        
        # 总支出
        self.lbl_expense = QLabel("总支出: ¥ 0.00")
        self.lbl_expense.setAlignment(Qt.AlignLeft)
        stats_layout.addWidget(self.lbl_expense)
        
        # 余额
        self.lbl_balance = QLabel("余额: ¥ 0.00")
        self.lbl_balance.setAlignment(Qt.AlignLeft)
        stats_layout.addWidget(self.lbl_balance)
        
        # 条目数
        self.lbl_count = QLabel("条目数: 0 条")
        self.lbl_count.setAlignment(Qt.AlignLeft)
        stats_layout.addWidget(self.lbl_count)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
        
        # 设置样式
        self.setStyleSheet("""
            QFrame {
                background: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                margin: 5px;
            }
            QLabel {
                color: #333;
                font-size: 14px;
                padding: 5px 0;
            }
        """)
        
        # 设置标签字体
        stat_font = QFont()
        stat_font.setPointSize(11)
        stat_font.setBold(True)
        
        self.lbl_income.setFont(stat_font)
        self.lbl_expense.setFont(stat_font)
        self.lbl_balance.setFont(stat_font)
        self.lbl_count.setFont(stat_font)
    
    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计信息
        
        Args:
            stats: 统计数据字典，包含 total_income, total_expense, balance, count
        """
        total_income = stats.get('total_income', 0.0)
        total_expense = stats.get('total_expense', 0.0)
        balance = stats.get('balance', 0.0)
        count = stats.get('count', 0)
        
        # 更新收入标签
        self.lbl_income.setText(f"总收入: ¥ {total_income:,.2f}")
        self.lbl_income.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # 更新支出标签
        self.lbl_expense.setText(f"总支出: ¥ {total_expense:,.2f}")
        self.lbl_expense.setStyleSheet("color: #F44336; font-weight: bold;")
        
        # 更新余额标签（根据正负设置颜色）
        self.lbl_balance.setText(f"结余: ¥ {balance:,.2f}")
        if balance > 0:
            balance_color = "#4CAF50"  # 绿色
        elif balance < 0:
            balance_color = "#F44336"  # 红色
        else:
            balance_color = "#757575"  # 灰色
        self.lbl_balance.setStyleSheet(f"color: {balance_color}; font-weight: bold;")
        
        # 更新条目数标签
        self.lbl_count.setText(f"条目数: {count} 条")
        self.lbl_count.setStyleSheet("color: #757575; font-weight: normal;")
    
    def clear_statistics(self):
        """清空统计信息"""
        self.update_statistics({
            'total_income': 0.0,
            'total_expense': 0.0,
            'balance': 0.0,
            'count': 0
        })