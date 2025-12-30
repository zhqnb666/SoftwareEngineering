import pytest
from datetime import date
from core.models import QueryFilters

class TestEntryManager:
    @pytest.fixture
    def sample_profile_id(self, db):
        """Create a sample profile and return its ID"""
        db.execute("INSERT INTO profiles (name) VALUES (?)", ("Test User",))
        row = db.fetchone("SELECT id FROM profiles WHERE name = ?", ("Test User",))
        return row["id"]

    def test_add_entry_success(self, entry_manager, sample_profile_id):
        """Test adding a valid entry"""
        entry = entry_manager.add_entry(
            profile_id=sample_profile_id,
            entry_date=date(2023, 1, 1),
            entry_type="支出",
            amount=100.0,
            category="餐饮",
            subcategory="午餐",
            note="测试备注"
        )
        
        assert entry.id is not None
        assert entry.amount == 100.0
        assert entry.category == "餐饮"
        assert entry.type == "支出"

    def test_add_entry_invalid_type(self, entry_manager, sample_profile_id):
        """Test adding entry with invalid type"""
        with pytest.raises(ValueError, match="条目类型必须是"):
            entry_manager.add_entry(
                profile_id=sample_profile_id,
                entry_date=date.today(),
                entry_type="无效类型",
                amount=100.0,
                category="餐饮"
            )

    def test_add_entry_negative_amount(self, entry_manager, sample_profile_id):
        """Test adding entry with negative amount"""
        with pytest.raises(ValueError, match="金额不能为负数"):
            entry_manager.add_entry(
                profile_id=sample_profile_id,
                entry_date=date.today(),
                entry_type="支出",
                amount=-50.0,
                category="餐饮"
            )

    def test_add_entry_empty_category(self, entry_manager, sample_profile_id):
        """Test adding entry with empty category"""
        with pytest.raises(ValueError, match="一级分类不能为空"):
            entry_manager.add_entry(
                profile_id=sample_profile_id,
                entry_date=date.today(),
                entry_type="支出",
                amount=100.0,
                category="   "
            )

    def test_get_entry_success(self, entry_manager, sample_profile_id):
        """Test retrieving an existing entry"""
        created = entry_manager.add_entry(
            profile_id=sample_profile_id,
            entry_date=date.today(),
            entry_type="收入",
            amount=5000.0,
            category="工资"
        )
        
        fetched = entry_manager.get_entry(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.amount == 5000.0

    def test_get_entry_not_found(self, entry_manager):
        """Test retrieving a non-existent entry"""
        assert entry_manager.get_entry(99999) is None

    def test_get_entries_filter(self, entry_manager, sample_profile_id):
        """Test filtering entries"""
        # Add some test data
        entry_manager.add_entry(sample_profile_id, date(2023, 1, 1), "支出", 100, "餐饮")
        entry_manager.add_entry(sample_profile_id, date(2023, 1, 2), "支出", 200, "交通")
        entry_manager.add_entry(sample_profile_id, date(2023, 1, 3), "收入", 1000, "工资")
        
        # Filter by type
        filters = QueryFilters(entry_type="支出")
        results = entry_manager.get_entries(sample_profile_id, filters)
        assert len(results) == 2
        assert all(e.type == "支出" for e in results)
        
        # Filter by date range
        filters = QueryFilters(start_date=date(2023, 1, 2), end_date=date(2023, 1, 3))
        results = entry_manager.get_entries(sample_profile_id, filters)
        assert len(results) == 2
        
        # Filter by category
        filters = QueryFilters(category="餐饮")
        results = entry_manager.get_entries(sample_profile_id, filters)
        assert len(results) == 1
        assert results[0].category == "餐饮"

    def test_delete_entry_success(self, entry_manager, sample_profile_id):
        """Test deleting an entry"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "测试"
        )
        
        assert entry_manager.delete_entry(entry.id) is True
        assert entry_manager.get_entry(entry.id) is None

    def test_delete_entry_fail(self, entry_manager):
        """Test deleting non-existent entry"""
        assert entry_manager.delete_entry(99999) is False

    def test_update_entry_success(self, entry_manager, sample_profile_id):
        """Test updating an entry"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "餐饮"
        )
        
        success = entry_manager.update_entry(
            entry.id,
            amount=200.0,
            note="修改后的备注"
        )
        
        assert success is True
        updated = entry_manager.get_entry(entry.id)
        assert updated.amount == 200.0
        assert updated.note == "修改后的备注"
        # Unchanged fields should remain
        assert updated.category == "餐饮"

    def test_update_entry_invalid(self, entry_manager, sample_profile_id):
        """Test updating with invalid data"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "餐饮"
        )
        
        with pytest.raises(ValueError):
            entry_manager.update_entry(entry.id, amount=-100)

    def test_get_statistics(self, entry_manager, sample_profile_id):
        """Test statistics calculation"""
        entry_manager.add_entry(sample_profile_id, date.today(), "收入", 1000, "工资")
        entry_manager.add_entry(sample_profile_id, date.today(), "支出", 200, "餐饮")
        entry_manager.add_entry(sample_profile_id, date.today(), "支出", 100, "交通")
        
        stats = entry_manager.get_statistics(sample_profile_id)
        
        assert stats.total_income == 1000
        assert stats.total_expense == 300
        assert stats.balance == 700
        assert stats.count == 3

    def test_get_entry_count(self, entry_manager, sample_profile_id):
        """Test getting entry count"""
        assert entry_manager.get_entry_count(sample_profile_id) == 0
        
        entry_manager.add_entry(sample_profile_id, date.today(), "支出", 100, "餐饮")
        assert entry_manager.get_entry_count(sample_profile_id) == 1

    def test_add_entry_db_error(self, entry_manager, sample_profile_id, monkeypatch):
        """Test database error during entry addition"""
        def mock_execute(*args, **kwargs):
            raise Exception("DB Error")
            
        monkeypatch.setattr(entry_manager.db, "execute", mock_execute)
        
        with pytest.raises(RuntimeError, match="添加条目失败"):
            entry_manager.add_entry(
                sample_profile_id, date.today(), "支出", 100, "餐饮"
            )

    def test_update_entry_no_fields(self, entry_manager, sample_profile_id):
        """Test updating entry with no fields provided"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "餐饮"
        )
        assert entry_manager.update_entry(entry.id) is True

    def test_update_entry_invalid_type(self, entry_manager, sample_profile_id):
        """Test updating entry with invalid type"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "餐饮"
        )
        with pytest.raises(ValueError, match="条目类型必须是"):
            entry_manager.update_entry(entry.id, entry_type="无效")

    def test_update_entry_empty_category(self, entry_manager, sample_profile_id):
        """Test updating entry with empty category"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "餐饮"
        )
        with pytest.raises(ValueError, match="一级分类不能为空"):
            entry_manager.update_entry(entry.id, category="   ")

    def test_update_entry_db_error(self, entry_manager, sample_profile_id, monkeypatch):
        """Test database error during entry update"""
        entry = entry_manager.add_entry(
            sample_profile_id, date.today(), "支出", 100, "餐饮"
        )
        
        def mock_execute(*args, **kwargs):
            # Only raise error for UPDATE, not for initial INSERT
            if "UPDATE" in args[0]:
                raise Exception("DB Error")
            return entry.id
            
        monkeypatch.setattr(entry_manager.db, "execute", mock_execute)
        
        assert entry_manager.update_entry(entry.id, amount=200) is False

    def test_get_statistics_with_filters(self, entry_manager, sample_profile_id):
        """Test statistics with filters"""
        entry_manager.add_entry(sample_profile_id, date(2023, 1, 1), "收入", 1000, "工资")
        entry_manager.add_entry(sample_profile_id, date(2023, 1, 2), "支出", 200, "餐饮")
        entry_manager.add_entry(sample_profile_id, date(2023, 1, 3), "支出", 100, "交通")
        
        # Filter by date
        filters = QueryFilters(start_date=date(2023, 1, 2))
        stats = entry_manager.get_statistics(sample_profile_id, filters)
        assert stats.total_income == 0
        assert stats.total_expense == 300
        
        # Filter by category
        filters = QueryFilters(category="餐饮")
        stats = entry_manager.get_statistics(sample_profile_id, filters)
        assert stats.total_expense == 200
