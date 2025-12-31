"""
分类管理模块
提供分类的查询和管理功能
"""

import logging
import sqlite3
from typing import Dict, List

from .database import Database
from .models import Category


class CategoryManager:
    """分类管理器"""

    def __init__(self, db: Database):
        """初始化分类管理器

        Args:
            db: 数据库连接实例
        """
        self.db = db

    def init_default_categories(self):
        """初始化默认分类"""
        # 默认收入分类
        income_categories = ["工资", "奖金", "红包", "投资收益", "其他"]

        # 默认支出分类及其子分类
        expense_categories = {
            "餐饮": ["早餐", "午餐", "晚餐", "零食"],
            "交通": ["公交", "地铁", "打车", "加油"],
            "购物": ["服饰", "日用品", "电子产品"],
            "娱乐": ["电影", "游戏", "旅游"],
            "医疗": ["药品", "门诊", "体检"],
            "教育": ["书籍", "课程", "培训"],
            "住房": ["房租", "水电", "物业"],
            "其他": [],
        }

        logger = logging.getLogger(__name__)

        try:
            # 添加收入分类
            for category in income_categories:
                try:
                    self.db.execute(
                        "INSERT OR IGNORE INTO categories (name, parent) VALUES (?, ?)",
                        (category, None),
                    )
                except sqlite3.Error as e:
                    logger.warning("插入收入分类 '%s' 失败: %s", category, e)

            # 添加支出分类及子分类
            for parent_category, subcategories in expense_categories.items():
                # 添加一级分类
                try:
                    self.db.execute(
                        "INSERT OR IGNORE INTO categories (name, parent) VALUES (?, ?)",
                        (parent_category, None),
                    )
                except sqlite3.Error as e:
                    logger.warning("插入一级分类 '%s' 失败: %s", parent_category, e)

                # 添加二级分类
                for subcategory in subcategories:
                    try:
                        self.db.execute(
                            "INSERT OR IGNORE INTO categories (name, parent) VALUES (?, ?)",
                            (subcategory, parent_category),
                        )
                    except sqlite3.Error as e:
                        logger.warning(
                            "插入二级分类 '%s' (父: %s) 失败: %s",
                            subcategory,
                            parent_category,
                            e,
                        )

            self.db.commit()
            logger.info("默认分类初始化完成")

        except Exception as e:
            self.db.rollback()
            logger.exception("初始化默认分类失败: %s", e)

    def get_categories(self, parent: str = None) -> List[Category]:
        """获取分类列表

        Args:
            parent: 父级分类名称，None 表示获取一级分类

        Returns:
            分类列表
        """
        if parent is None:
            # 获取一级分类
            sql = "SELECT * FROM categories WHERE parent IS NULL ORDER BY name"
            params = ()
        else:
            # 获取指定父级的子分类
            sql = "SELECT * FROM categories WHERE parent = ? ORDER BY name"
            params = (parent,)

        rows = self.db.fetchall(sql, params)

        categories = []
        for row in rows:
            categories.append(
                Category(id=row["id"], name=row["name"], parent=row["parent"])
            )

        return categories

    def get_all_categories(self) -> List[Category]:
        """获取所有分类

        Returns:
            所有分类列表
        """
        rows = self.db.fetchall("SELECT * FROM categories ORDER BY parent, name")

        categories = []
        for row in rows:
            categories.append(
                Category(id=row["id"], name=row["name"], parent=row["parent"])
            )

        return categories

    def get_categories_by_type(self, entry_type: str) -> Dict[str, List[str]]:
        """根据条目类型获取分类结构

        Args:
            entry_type: 条目类型（'收入' 或 '支出'）

        Returns:
            分类字典，key 为一级分类，value 为二级分类列表
        """
        # 获取适合该类型的一级分类
        if entry_type == "收入":
            # 收入分类：工资、奖金、红包、投资收益、其他
            primary_categories = ["工资", "奖金", "红包", "投资收益", "其他"]
        else:
            # 支出分类：餐饮、交通、购物、娱乐、医疗、教育、住房、其他
            primary_categories = [
                "餐饮",
                "交通",
                "购物",
                "娱乐",
                "医疗",
                "教育",
                "住房",
                "其他",
            ]

        result = {}

        for category in primary_categories:
            # 获取该一级分类下的所有二级分类
            subcategories = self.get_categories(category)
            subcategory_names = [sub.name for sub in subcategories]
            result[category] = subcategory_names

        return result

    def add_category(self, name: str, parent: str = None) -> Category:
        """添加新分类

        Args:
            name: 分类名称
            parent: 父级分类名称（可选）

        Returns:
            新创建的分类对象

        Raises:
            ValueError: 分类已存在
        """
        # 检查分类是否已存在
        if parent is None:
            existing = self.db.fetchone(
                "SELECT id FROM categories WHERE name = ? AND parent IS NULL", (name,)
            )
        else:
            existing = self.db.fetchone(
                "SELECT id FROM categories WHERE name = ? AND parent = ?", (name, parent)
            )

        if existing:
            raise ValueError(f"分类 '{name}' 已存在")

        try:
            category_id = self.db.execute(
                "INSERT INTO categories (name, parent) VALUES (?, ?)", (name, parent)
            )

            self.db.commit()

            return Category(id=category_id, name=name, parent=parent)

        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"添加分类失败: {e}")

    def delete_category(self, category_id: int) -> bool:
        """删除分类

        Args:
            category_id: 分类 ID

        Returns:
            删除是否成功
        """
        try:
            rows_affected = self.db.execute(
                "DELETE FROM categories WHERE id = ?", (category_id,)
            )

            self.db.commit()
            return rows_affected > 0

        except Exception as e:
            self.db.rollback()
            print(f"删除分类失败: {e}")
            return False

    def get_category_by_name(self, name: str, parent: str = None) -> Category:
        """根据名称获取分类

        Args:
            name: 分类名称
            parent: 父级分类名称

        Returns:
            分类对象或 None
        """
        if parent is None:
            row = self.db.fetchone(
                "SELECT * FROM categories WHERE name = ? AND parent IS NULL", (name,)
            )
        else:
            row = self.db.fetchone(
                "SELECT * FROM categories WHERE name = ? AND parent = ?", (name, parent)
            )

        if row:
            return Category(id=row["id"], name=row["name"], parent=row["parent"])
        return None
