"""
条目管理模块
提供条目的增删查和统计功能
"""

import logging
from datetime import date
from typing import List, Optional

from .database import Database
from .models import Entry, QueryFilters, Statistics


class EntryManager:
    """条目管理器"""

    def __init__(self, db: Database):
        """初始化条目管理器

        Args:
            db: 数据库连接实例
        """
        self.db = db

    def add_entry(
        self,
        profile_id: int,
        entry_date: date,
        entry_type: str,
        amount: float,
        category: str,
        subcategory: str = None,
        note: str = None,
    ) -> Entry:
        """添加新条目

        Args:
            profile_id: 账户 ID
            entry_date: 记录日期
            entry_type: 类型（'收入' 或 '支出'）
            amount: 金额
            category: 一级分类
            subcategory: 二级分类（可选）
            note: 备注（可选）

        Returns:
            新创建的条目对象

        Raises:
            ValueError: 参数验证失败
        """
        # 参数验证
        if entry_type not in ("收入", "支出"):
            raise ValueError("条目类型必须是 '收入' 或 '支出'")

        if amount < 0:
            raise ValueError("金额不能为负数")

        if not category.strip():
            raise ValueError("一级分类不能为空")

        try:
            # 插入新条目
            entry_id = self.db.execute(
                """INSERT INTO entries 
                   (profile_id, date, type, amount, category, subcategory, note) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    profile_id,
                    entry_date.isoformat(),
                    entry_type,
                    amount,
                    category.strip(),
                    subcategory.strip() if subcategory else None,
                    note.strip() if note else None,
                ),
            )

            self.db.commit()

            # 返回新创建的条目
            return self.get_entry(entry_id)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"添加条目失败: {e}")

    def get_entry(self, entry_id: int) -> Optional[Entry]:
        """根据 ID 获取条目

        Args:
            entry_id: 条目 ID

        Returns:
            条目对象或 None
        """
        row = self.db.fetchone("SELECT * FROM entries WHERE id = ?", (entry_id,))

        if row:
            return Entry(
                id=row["id"],
                profile_id=row["profile_id"],
                date=date.fromisoformat(row["date"]),
                type=row["type"],
                amount=row["amount"],
                category=row["category"],
                subcategory=row["subcategory"],
                note=row["note"],
            )
        return None

    def get_entries(self, profile_id: int, filters: QueryFilters = None) -> List[Entry]:
        """获取条目列表

        Args:
            profile_id: 账户 ID
            filters: 查询筛选条件

        Returns:
            条目列表，按日期倒序排列
        """
        # 构建查询条件
        where_conditions = ["profile_id = ?"]
        params = [profile_id]

        if filters:
            if filters.start_date:
                where_conditions.append("date >= ?")
                params.append(filters.start_date.isoformat())

            if filters.end_date:
                where_conditions.append("date <= ?")
                params.append(filters.end_date.isoformat())

            if filters.entry_type:
                where_conditions.append("type = ?")
                params.append(filters.entry_type)

            if filters.category:
                where_conditions.append("category = ?")
                params.append(filters.category)

        # 执行查询
        sql = f"""
            SELECT * FROM entries 
            WHERE {' AND '.join(where_conditions)} 
            ORDER BY date DESC, id DESC
        """

        rows = self.db.fetchall(sql, tuple(params))

        entries = []
        for row in rows:
            entries.append(
                Entry(
                    id=row["id"],
                    profile_id=row["profile_id"],
                    date=date.fromisoformat(row["date"]),
                    type=row["type"],
                    amount=row["amount"],
                    category=row["category"],
                    subcategory=row["subcategory"],
                    note=row["note"],
                )
            )

        return entries

    def delete_entry(self, entry_id: int) -> bool:
        """删除条目

        Args:
            entry_id: 条目 ID

        Returns:
            删除是否成功
        """
        try:
            rows_affected = self.db.execute(
                "DELETE FROM entries WHERE id = ?", (entry_id,)
            )

            self.db.commit()
            return rows_affected > 0

        except Exception as e:
            self.db.rollback()
            logging.getLogger(__name__).exception("删除条目失败: %s", e)
            return False

    def get_statistics(
        self, profile_id: int, filters: QueryFilters = None
    ) -> Statistics:
        """获取统计信息

        Args:
            profile_id: 账户 ID
            filters: 查询筛选条件

        Returns:
            统计数据
        """
        # 构建查询条件
        where_conditions = ["profile_id = ?"]
        params = [profile_id]

        if filters:
            if filters.start_date:
                where_conditions.append("date >= ?")
                params.append(filters.start_date.isoformat())

            if filters.end_date:
                where_conditions.append("date <= ?")
                params.append(filters.end_date.isoformat())

            if filters.entry_type:
                where_conditions.append("type = ?")
                params.append(filters.entry_type)

            if filters.category:
                where_conditions.append("category = ?")
                params.append(filters.category)

        where_clause = " AND ".join(where_conditions)

        # 查询收入统计
        income_sql = f"""
            SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count 
            FROM entries 
            WHERE {where_clause} AND type = '收入'
        """
        income_row = self.db.fetchone(income_sql, tuple(params))
        total_income = income_row["total"] if income_row else 0
        income_count = income_row["count"] if income_row else 0

        # 查询支出统计
        expense_sql = f"""
            SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count 
            FROM entries 
            WHERE {where_clause} AND type = '支出'
        """
        expense_row = self.db.fetchone(expense_sql, tuple(params))
        total_expense = expense_row["total"] if expense_row else 0
        expense_count = expense_row["count"] if expense_row else 0

        return Statistics(
            total_income=total_income,
            total_expense=total_expense,
            balance=total_income - total_expense,
            count=income_count + expense_count,
        )

    def get_entry_count(self, profile_id: int) -> int:
        """获取指定账户的条目总数

        Args:
            profile_id: 账户 ID

        Returns:
            条目总数
        """
        row = self.db.fetchone(
            "SELECT COUNT(*) as count FROM entries WHERE profile_id = ?", (profile_id,)
        )
        return row["count"] if row else 0

    def update_entry(
        self,
        entry_id: int,
        entry_date: date = None,
        entry_type: str = None,
        amount: float = None,
        category: str = None,
        subcategory: str = None,
        note: str = None,
    ) -> bool:
        """更新条目信息

        Args:
            entry_id: 条目 ID
            entry_date: 新的记录日期（可选）
            entry_type: 新的类型（可选）
            amount: 新的金额（可选）
            category: 新的一级分类（可选）
            subcategory: 新的二级分类（可选）
            note: 新的备注（可选）

        Returns:
            更新是否成功
        """
        # 收集要更新的字段
        update_fields = []
        params = []

        if entry_date is not None:
            update_fields.append("date = ?")
            params.append(entry_date.isoformat())

        if entry_type is not None:
            if entry_type not in ("收入", "支出"):
                raise ValueError("条目类型必须是 '收入' 或 '支出'")
            update_fields.append("type = ?")
            params.append(entry_type)

        if amount is not None:
            if amount < 0:
                raise ValueError("金额不能为负数")
            update_fields.append("amount = ?")
            params.append(amount)

        if category is not None:
            if not category.strip():
                raise ValueError("一级分类不能为空")
            update_fields.append("category = ?")
            params.append(category.strip())

        if subcategory is not None:
            update_fields.append("subcategory = ?")
            params.append(subcategory.strip() if subcategory else None)

        if note is not None:
            update_fields.append("note = ?")
            params.append(note.strip() if note else None)

        if not update_fields:
            return True  # 没有要更新的内容

        try:
            params.append(entry_id)
            sql = f"UPDATE entries SET {', '.join(update_fields)} WHERE id = ?"

            rows_affected = self.db.execute(sql, tuple(params))
            self.db.commit()

            return rows_affected > 0

        except Exception as e:
            self.db.rollback()
            logging.getLogger(__name__).exception("更新条目失败: %s", e)
            return False
