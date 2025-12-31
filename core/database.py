"""
数据库连接管理模块
提供 SQLite 数据库连接管理和基础操作
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Tuple


# 注册适配器以消除 Python 3.12+ 的 DeprecationWarning
def adapt_date(val):
    return val.isoformat()


def adapt_datetime(val):
    return val.isoformat(" ")


sqlite3.register_adapter(date, adapt_date)
sqlite3.register_adapter(datetime, adapt_datetime)


class Database:
    """数据库连接管理"""

    def __init__(self, db_path: str):
        """初始化数据库连接

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._ensure_db_dir()
        self._connect()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        """建立数据库连接"""
        try:
            # 启用线程安全模式
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 支持字典式访问
            print(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    def init_db(self):
        """初始化数据库表结构"""
        try:
            # 创建账户表
            self.execute(
                """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # 创建分类表
            self.execute(
                """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent TEXT,
                UNIQUE(name, parent)
            )
            """
            )

            # 创建条目表
            self.execute(
                """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                date DATE NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('收入', '支出')),
                amount REAL NOT NULL CHECK(amount >= 0),
                category TEXT NOT NULL,
                subcategory TEXT,
                note TEXT,
                FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            )
            """
            )

            # 创建索引
            self.execute(
                "CREATE INDEX IF NOT EXISTS idx_entries_profile ON entries(profile_id)"
            )
            self.execute("CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date)")
            self.execute("CREATE INDEX IF NOT EXISTS idx_entries_type ON entries(type)")

            # 启用外键约束
            self.execute("PRAGMA foreign_keys = ON")

            self.commit()
            print("数据库表结构初始化完成")

        except Exception as e:
            print(f"数据库初始化失败: {e}")
            self.rollback()
            raise

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("数据库连接已关闭")

    def execute(self, sql: str, params: Tuple = ()) -> int:
        """执行 SQL 语句

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            影响的行数或新插入记录的 ID
        """
        if not self.conn:
            raise RuntimeError("数据库连接未建立")

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)

            # 如果是 INSERT 语句，返回新记录的 ID
            if sql.strip().upper().startswith("INSERT"):
                return cursor.lastrowid

            return cursor.rowcount

        except Exception as e:
            print(f"SQL 执行失败: {sql}")
            print(f"错误信息: {e}")
            raise

    def fetchall(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """执行查询并返回所有结果

        Args:
            sql: 查询 SQL
            params: 参数元组

        Returns:
            查询结果列表
        """
        if not self.conn:
            raise RuntimeError("数据库连接未建立")

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            print(f"查询失败: {sql}")
            print(f"错误信息: {e}")
            raise

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """执行查询并返回第一条结果

        Args:
            sql: 查询 SQL
            params: 参数元组

        Returns:
            查询结果或 None
        """
        if not self.conn:
            raise RuntimeError("数据库连接未建立")

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()
        except Exception as e:
            print(f"查询失败: {sql}")
            print(f"错误信息: {e}")
            raise

    def begin_transaction(self):
        """开始事务"""
        if not self.conn:
            raise RuntimeError("数据库连接未建立")
        self.execute("BEGIN")

    def commit(self):
        """提交事务"""
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """回滚事务"""
        if self.conn:
            self.conn.rollback()


def get_default_db_path() -> str:
    """获取默认数据库路径"""
    current_dir = Path(__file__).parent.parent
    data_dir = current_dir / "data"
    return str(data_dir / "accounting.db")
