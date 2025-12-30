import pytest
import os
import tempfile
import csv
from unittest.mock import MagicMock, patch
from core.importer import DataImporter
from core.category_manager import CategoryManager

class TestImporter:
    @pytest.fixture
    def importer(self, db):
        category_mgr = CategoryManager(db)
        return DataImporter(db, category_mgr)

    @pytest.fixture
    def profile(self, profile_manager):
        return profile_manager.create_profile("Import User")

    def create_csv_file(self, content, encoding='utf-8'):
        """Helper to create a temp CSV file"""
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, 'w', encoding=encoding, newline='') as f:
            f.write(content)
        return path

    def test_validate_csv_valid(self, importer):
        """Test validating a valid CSV file"""
        content = "日期,类型,金额,分类\n2023-01-01,收入,5000,工资"
        path = self.create_csv_file(content)
        try:
            valid, errors = importer.validate_csv(path)
            assert valid is True
            assert len(errors) == 0
        finally:
            os.remove(path)

    def test_validate_csv_missing_header(self, importer):
        """Test validating CSV with missing headers"""
        content = "日期,类型,金额\n2023-01-01,收入,5000"
        path = self.create_csv_file(content)
        try:
            valid, errors = importer.validate_csv(path)
            assert valid is False
            assert any("缺少必需的列" in e for e in errors)
        finally:
            os.remove(path)

    def test_validate_csv_empty(self, importer):
        """Test validating empty CSV"""
        path = self.create_csv_file("")
        try:
            valid, errors = importer.validate_csv(path)
            assert valid is False
            assert "文件为空或格式不正确" in errors
        finally:
            os.remove(path)

    def test_validate_csv_no_data(self, importer):
        """Test validating CSV with header but no data"""
        content = "日期,类型,金额,分类\n"
        path = self.create_csv_file(content)
        try:
            valid, errors = importer.validate_csv(path)
            assert valid is False
            assert "文件中没有数据行" in errors
        finally:
            os.remove(path)

    def test_validate_csv_file_not_found(self, importer):
        """Test validating non-existent file"""
        valid, errors = importer.validate_csv("non_existent_file.csv")
        assert valid is False
        assert "文件不存在" in errors

    def test_validate_csv_encoding_error(self, importer):
        """Test validating file with bad encoding"""
        # Create a file with GBK encoding but try to read as UTF-8 (default in code)
        content = "日期,类型,金额,分类\n2023-01-01,收入,5000,工资"
        path = self.create_csv_file(content, encoding='gbk')
        # Write some chinese characters that are valid in GBK but invalid in UTF-8
        with open(path, 'wb') as f:
            f.write("日期,类型,金额,分类\n".encode('gbk'))
            f.write("2023-01-01,收入,5000,测试\n".encode('gbk'))
            
        try:
            valid, errors = importer.validate_csv(path)
            assert valid is False
            assert "文件编码错误" in errors[0]
        finally:
            os.remove(path)

    def test_validate_csv_generic_error(self, importer, monkeypatch):
        """Test generic exception during validation"""
        def mock_open(*args, **kwargs):
            raise Exception("Generic Error")
        
        monkeypatch.setattr("builtins.open", mock_open)
        
        valid, errors = importer.validate_csv("some_file.csv")
        assert valid is False
        assert any("Generic Error" in e for e in errors)

    def test_import_from_csv_success(self, importer, profile):
        """Test successful import"""
        content = "日期,类型,金额,分类,子分类,备注\n2023-01-01,收入,5000,工资,,\n2023-01-02,支出,100,餐饮,午餐,好吃"
        path = self.create_csv_file(content)
        try:
            count, errors = importer.import_from_csv(profile.id, path)
            assert count == 2
            assert len(errors) == 0
        finally:
            os.remove(path)

    def test_import_from_csv_validation_fail(self, importer, profile):
        """Test import fails validation"""
        content = "日期,类型\n"
        path = self.create_csv_file(content)
        try:
            count, errors = importer.import_from_csv(profile.id, path)
            assert count == 0
            assert len(errors) > 0
        finally:
            os.remove(path)

    def test_import_from_csv_row_errors(self, importer, profile):
        """Test import with some invalid rows"""
        # First row valid, second invalid date, third invalid amount
        content = "日期,类型,金额,分类\n2023-01-01,收入,5000,工资\ninvalid-date,支出,100,餐饮\n2023-01-03,支出,invalid,交通"
        path = self.create_csv_file(content)
        try:
            count, errors = importer.import_from_csv(profile.id, path)
            assert count == 1 # Only first row imported
            assert len(errors) == 2 # Two errors
        finally:
            os.remove(path)

    def test_import_db_error(self, importer, profile, monkeypatch):
        """Test database error during import"""
        content = "日期,类型,金额,分类\n2023-01-01,收入,5000,工资"
        path = self.create_csv_file(content)
        
        # Mock EntryManager.add_entry to raise exception
        def mock_add_entry(*args, **kwargs):
            raise Exception("DB Error")
            
        # We need to patch the EntryManager instance that is used inside import_from_csv
        # Since we are using in-memory DB, it uses self.entry_mgr
        monkeypatch.setattr(importer.entry_mgr, "add_entry", mock_add_entry)
        
        try:
            count, errors = importer.import_from_csv(profile.id, path)
            assert count == 0
            assert len(errors) > 0
            assert "DB Error" in errors[0]
        finally:
            os.remove(path)

    def test_save_template_csv(self, importer):
        """Test saving template CSV"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            path = tmp.name
            
        try:
            success = importer.save_template_csv(path)
            assert success is True
            assert os.path.exists(path)
            with open(path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                assert "日期,类型,金额,分类" in content
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_save_template_error(self, importer, monkeypatch):
        """Test error saving template"""
        def mock_open(*args, **kwargs):
            raise Exception("Write Error")
            
        monkeypatch.setattr("builtins.open", mock_open)
        
        success = importer.save_template_csv("some_path.csv")
        assert success is False
