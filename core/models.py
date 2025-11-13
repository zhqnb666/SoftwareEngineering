"""
数据模型定义
定义系统中的数据结构
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Optional


@dataclass
class Profile:
    """账户模型"""

    id: int
    name: str
    description: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class Entry:
    """条目模型"""

    id: int
    profile_id: int
    date: date
    type: str  # '收入' 或 '支出'
    amount: float
    category: str
    subcategory: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "date": self.date.isoformat() if self.date else None,
            "type": self.type,
            "amount": self.amount,
            "category": self.category,
            "subcategory": self.subcategory,
            "note": self.note,
        }


@dataclass
class Category:
    """分类模型"""

    id: int
    name: str
    parent: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {"id": self.id, "name": self.name, "parent": self.parent}


@dataclass
class Statistics:
    """统计数据模型"""

    total_income: float = 0.0
    total_expense: float = 0.0
    balance: float = 0.0
    count: int = 0

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total_income": self.total_income,
            "total_expense": self.total_expense,
            "balance": self.balance,
            "count": self.count,
        }


@dataclass
class QueryFilters:
    """查询筛选条件"""

    start_date: Optional[date] = None
    end_date: Optional[date] = None
    entry_type: Optional[str] = None  # None, '收入', '支出'
    category: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "entry_type": self.entry_type,
            "category": self.category,
        }
