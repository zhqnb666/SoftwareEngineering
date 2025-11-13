# coding: utf-8
"""
CSV 数据导出模块
提供条目数据的 CSV 导出功能
"""
import csv
from typing import List, Optional
from io import StringIO
import logging

from .database import Database
from .entry_manager import EntryManager
from .models import QueryFilters, Entry


class DataExporter:
    """CSV 数据导出器"""
    
    def __init__(self, db: Database):
        """初始化导出器
        
        Args:
            db: 数据库连接实例
        """
        self.db = db
        self.entry_mgr = EntryManager(db)
    
    def export_to_csv(self, profile_id: int, filepath: str, 
                      filters: QueryFilters = None) -> bool:
        """导出数据到 CSV 文件
        
        Args:
            profile_id: 账户 ID
            filepath: 导出文件路径
            filters: 查询筛选条件（可选）
            
        Returns:
            导出是否成功
        """
        try:
            # 获取条目数据
            entries = self.entry_mgr.get_entries(profile_id, filters)
            
            if not entries:
                logging.getLogger(__name__).info("没有数据可导出")
                return False
            
            # 生成 CSV 内容并保存
            csv_content = self._generate_csv_content(entries)
            
            # 使用 UTF-8 BOM 编码以支持 Excel 中文显示
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as file:
                file.write(csv_content)
            
            logging.getLogger(__name__).info("成功导出 %d 条记录到 %s", len(entries), filepath)
            return True
            
        except Exception as e:
            logging.getLogger(__name__).exception("导出失败: %s", e)
            return False
    
    def export_to_string(self, profile_id: int, 
                        filters: QueryFilters = None) -> Optional[str]:
        """导出数据为 CSV 字符串
        
        Args:
            profile_id: 账户 ID
            filters: 查询筛选条件（可选）
            
        Returns:
            CSV 字符串或 None
        """
        try:
            # 获取条目数据
            entries = self.entry_mgr.get_entries(profile_id, filters)
            
            if not entries:
                return None
            
            return self._generate_csv_content(entries)
            
        except Exception as e:
            logging.getLogger(__name__).exception("生成 CSV 字符串失败: %s", e)
            return None
    
    def _generate_csv_content(self, entries: List[Entry]) -> str:
        """生成 CSV 内容
        
        Args:
            entries: 条目列表
            
        Returns:
            CSV 字符串
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['日期', '类型', '金额', '一级分类', '二级分类', '备注'])
        
        # 写入数据行
        for entry in entries:
            writer.writerow([
                entry.date.isoformat(),  # 日期格式：YYYY-MM-DD
                entry.type,              # 类型：收入/支出
                f"{entry.amount:.2f}",   # 金额：保留2位小数
                entry.category,          # 一级分类
                entry.subcategory or '', # 二级分类（可能为空）
                entry.note or ''         # 备注（可能为空）
            ])
        
        return output.getvalue()
    
    def get_export_summary(self, profile_id: int, 
                          filters: QueryFilters = None) -> dict:
        """获取导出数据摘要
        
        Args:
            profile_id: 账户 ID
            filters: 查询筛选条件（可选）
            
        Returns:
            摘要信息字典
        """
        try:
            # 获取条目数据和统计信息
            entries = self.entry_mgr.get_entries(profile_id, filters)
            statistics = self.entry_mgr.get_statistics(profile_id, filters)
            
            return {
                'total_count': len(entries),
                'income_count': len([e for e in entries if e.type == '收入']),
                'expense_count': len([e for e in entries if e.type == '支出']),
                'total_income': statistics.total_income,
                'total_expense': statistics.total_expense,
                'date_range': self._get_date_range(entries)
            }
            
        except Exception as e:
            logging.getLogger(__name__).exception("获取导出摘要失败: %s", e)
            return {}
    
    def _get_date_range(self, entries: List[Entry]) -> tuple:
        """获取条目的日期范围
        
        Args:
            entries: 条目列表
            
        Returns:
            (最早日期, 最晚日期) 或 (None, None)
        """
        if not entries:
            return None, None
        
        dates = [entry.date for entry in entries]
        return min(dates), max(dates)