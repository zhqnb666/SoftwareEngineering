import pytest
import os
import tempfile
from datetime import date
from core.exporter import DataExporter
from core.models import QueryFilters

class TestExporter:
    @pytest.fixture
    def exporter(self, db):
        return DataExporter(db)

    @pytest.fixture
    def sample_data(self, entry_manager, profile_manager):
        """Create sample data for export tests"""
        profile = profile_manager.create_profile("Export User")
        
        entry_manager.add_entry(
            profile.id, date(2023, 1, 1), "收入", 5000, "工资", note="一月工资"
        )
        entry_manager.add_entry(
            profile.id, date(2023, 1, 2), "支出", 100, "餐饮", "午餐"
        )
        
        return profile

    def test_export_to_string(self, exporter, sample_data):
        """Test exporting to string"""
        csv_str = exporter.export_to_string(sample_data.id)
        
        assert csv_str is not None
        # Header might vary slightly but should contain these
        assert "日期" in csv_str
        assert "类型" in csv_str
        assert "金额" in csv_str
        assert "一级分类" in csv_str
        
        # Check data presence
        assert "2023-01-01,收入,5000.00,工资" in csv_str
        assert "2023-01-02,支出,100.00,餐饮" in csv_str

    def test_export_to_csv_file(self, exporter, sample_data):
        """Test exporting to file"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            path = tmp.name
            
        try:
            success = exporter.export_to_csv(sample_data.id, path)
            assert success is True
            assert os.path.exists(path)
            
            with open(path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                assert "日期" in content
                assert "5000.00" in content
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_export_with_filters(self, exporter, sample_data):
        """Test exporting with filters"""
        filters = QueryFilters(entry_type="支出")
        csv_str = exporter.export_to_string(sample_data.id, filters)
        
        assert csv_str is not None
        assert "支出" in csv_str
        assert "收入" not in csv_str

    def test_export_no_data(self, exporter, profile_manager):
        """Test exporting when no data exists"""
        empty_profile = profile_manager.create_profile("Empty User")
        
        assert exporter.export_to_string(empty_profile.id) is None
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            path = tmp.name
            
        try:
            assert exporter.export_to_csv(empty_profile.id, path) is False
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_export_error(self, exporter, sample_data, monkeypatch):
        """Test error handling during export"""
        def mock_generate(*args, **kwargs):
            raise Exception("Export Error")
            
        monkeypatch.setattr(exporter, "_generate_csv_content", mock_generate)
        
        assert exporter.export_to_string(sample_data.id) is None
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            path = tmp.name
        try:
            assert exporter.export_to_csv(sample_data.id, path) is False
        finally:
            if os.path.exists(path):
                os.remove(path)
