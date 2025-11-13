"""
CSV 数据导入模块
提供 CSV 文件的验证和导入功能
"""

import csv
import logging
from datetime import datetime
from io import StringIO
from typing import Dict, List, Tuple

from .category_manager import CategoryManager
from .database import Database
from .entry_manager import EntryManager


class DataImporter:
    """CSV 数据导入器"""

    def __init__(self, db: Database, category_mgr: CategoryManager):
        """初始化导入器

        Args:
            db: 数据库连接实例
            category_mgr: 分类管理器
        """
        self.db = db
        self.category_mgr = category_mgr
        self.entry_mgr = EntryManager(db)

        # CSV 文件必需的表头
        self.required_headers = ["日期", "类型", "金额", "分类"]

    def validate_csv(self, filepath: str) -> Tuple[bool, List[str]]:
        """验证 CSV 文件格式

        Args:
            filepath: CSV 文件路径

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        logger = logging.getLogger(__name__)

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                # 尝试检测文件编码和分隔符（不需要保留全文）
                _ = file.read(0)

            # 重新打开文件进行解析
            with open(filepath, "r", encoding="utf-8") as file:
                # 检测CSV分隔符
                sniffer = csv.Sniffer()
                sample = file.read(1024)
                file.seek(0)

                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except csv.Error:
                    delimiter = ","

                reader = csv.DictReader(file, delimiter=delimiter)

                # 验证表头
                if not reader.fieldnames:
                    errors.append("文件为空或格式不正确")
                    return False, errors

                # 检查必需的列
                missing_headers = []
                for header in self.required_headers:
                    if header not in reader.fieldnames:
                        missing_headers.append(header)

                if missing_headers:
                    errors.append(f"缺少必需的列: {', '.join(missing_headers)}")
                    return False, errors

                # 验证每一行数据
                line_num = 2  # 从第2行开始计算（第1行是表头）

                for row in reader:
                    row_errors = self._validate_row(row, line_num)
                    errors.extend(row_errors)
                    line_num += 1

                # 如果没有数据行
                if line_num == 2:
                    errors.append("文件中没有数据行")
                    return False, errors

        except FileNotFoundError:
            errors.append("文件不存在")
            return False, errors
        except UnicodeDecodeError:
            errors.append("文件编码错误，请使用 UTF-8 编码")
            return False, errors
        except Exception as e:
            logger.exception("validate_csv 读取文件出错: %s", e)
            errors.append(f"文件读取错误: {str(e)}")
            return False, errors

        return len(errors) == 0, errors

    def import_from_csv(self, profile_id: int, filepath: str) -> Tuple[int, List[str]]:
        """从 CSV 文件导入数据

        Args:
            profile_id: 目标账户 ID
            filepath: CSV 文件路径

        Returns:
            (成功导入的条目数, 错误信息列表)
        """
        # 首先验证文件
        is_valid, errors = self.validate_csv(filepath)
        if not is_valid:
            return 0, errors

        imported_count = 0
        import_errors = []

        # 为当前线程创建新的数据库连接（如果是内存数据库则重用原连接）
        from .category_manager import CategoryManager
        from .database import Database

        if self.db.db_path == ":memory:":
            # 内存数据库不能跨线程共享，直接使用原连接
            thread_db = self.db
            thread_entry_mgr = self.entry_mgr
        else:
            # 文件数据库可以创建新连接
            thread_db = Database(self.db.db_path)
            thread_db.init_db()  # 确保表结构已创建
            thread_category_mgr = CategoryManager(thread_db)
            thread_category_mgr.init_default_categories()  # 初始化默认分类
            thread_entry_mgr = EntryManager(thread_db)

        logger = logging.getLogger(__name__)

        try:
            thread_db.begin_transaction()

            with open(filepath, "r", encoding="utf-8") as file:
                # 检测分隔符
                sniffer = csv.Sniffer()
                sample = file.read(1024)
                file.seek(0)

                try:
                    delimiter = sniffer.sniff(sample).delimiter
                except csv.Error:
                    delimiter = ","

                reader = csv.DictReader(file, delimiter=delimiter)
                line_num = 2

                for row in reader:
                    try:
                        # 解析数据
                        entry_date = datetime.strptime(
                            row["日期"].strip(), "%Y-%m-%d"
                        ).date()
                        entry_type = row["类型"].strip()
                        amount = float(row["金额"].strip())
                        category = row["分类"].strip()
                        subcategory = (
                            row.get("子分类", "").strip()
                            if row.get("子分类", "").strip()
                            else None
                        )
                        note = (
                            row.get("备注", "").strip()
                            if row.get("备注", "").strip()
                            else None
                        )

                        # 添加条目
                        thread_entry_mgr.add_entry(
                            profile_id=profile_id,
                            entry_date=entry_date,
                            entry_type=entry_type,
                            amount=amount,
                            category=category,
                            subcategory=subcategory,
                            note=note,
                        )

                        imported_count += 1

                    except Exception as e:
                        logger.debug("第 %s 行导入失败: %s", line_num, e, exc_info=True)
                        import_errors.append(f"第 {line_num} 行导入失败: {str(e)}")

                    line_num += 1

            # 确保数据提交
            thread_db.commit()

            # 如果使用的是独立的数据库连接，强制刷新原始数据库连接
            if thread_db is not self.db:
                # 重新连接原始数据库以看到最新更改
                self.db.conn.execute("PRAGMA cache_size = 0")
                self.db.conn.execute("PRAGMA cache_size = -2000")

            logger.info("成功导入 %d 条记录", imported_count)

        except Exception as e:
            logger.exception("导入过程中发生错误: %s", e)
            thread_db.rollback()
            import_errors.append(f"导入过程中发生错误: {str(e)}")
        finally:
            # 只关闭非内存数据库连接
            if thread_db is not self.db:
                thread_db.close()

        return imported_count, import_errors

    def _validate_row(self, row: Dict[str, str], line_num: int) -> List[str]:
        """验证单行数据

        Args:
            row: CSV 行数据字典
            line_num: 行号

        Returns:
            错误信息列表
        """
        errors = []

        # 验证日期
        date_str = row.get("日期", "").strip()
        if not self._validate_date(date_str):
            errors.append(f"第 {line_num} 行：日期格式错误，应为 YYYY-MM-DD")

        # 验证类型
        type_str = row.get("类型", "").strip()
        if not self._validate_type(type_str):
            errors.append(f"第 {line_num} 行：类型必须是 '收入' 或 '支出'")

        # 验证金额
        amount_str = row.get("金额", "").strip()
        if not self._validate_amount(amount_str):
            errors.append(f"第 {line_num} 行：金额格式错误或为负数")

        # 验证分类
        category_str = row.get("分类", "").strip()
        if not category_str:
            errors.append(f"第 {line_num} 行：分类不能为空")

        return errors

    def _validate_date(self, date_str: str) -> bool:
        """验证日期格式"""
        if not date_str:
            return False

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _validate_type(self, type_str: str) -> bool:
        """验证类型"""
        return type_str in ("收入", "支出")

    def _validate_amount(self, amount_str: str) -> bool:
        """验证金额"""
        if not amount_str:
            return False

        try:
            amount = float(amount_str)
            return amount >= 0
        except ValueError:
            return False

    def get_template_csv(self) -> str:
        """获取 CSV 模板内容

        Returns:
            CSV 模板字符串
        """
        template_data = [
            ["日期", "类型", "金额", "分类", "子分类", "备注"],
            ["2025-01-15", "支出", "35.50", "餐饮", "午餐", "公司食堂"],
            ["2025-01-16", "收入", "5000.00", "工资", "", "月薪"],
            ["2025-01-17", "支出", "12.00", "交通", "地铁", "通勤费用"],
        ]

        output = StringIO()
        writer = csv.writer(output)
        writer.writerows(template_data)

        return output.getvalue()

    def save_template_csv(self, filepath: str) -> bool:
        """保存 CSV 模板文件

        Args:
            filepath: 保存路径

        Returns:
            保存是否成功
        """
        try:
            template_content = self.get_template_csv()
            # 使用 UTF-8 BOM 编码以支持 Excel 中文显示
            with open(filepath, "w", encoding="utf-8-sig", newline="") as file:
                file.write(template_content)
            return True
        except Exception as e:
            print(f"保存模板文件失败: {e}")
            return False
