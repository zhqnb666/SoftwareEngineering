import pytest
from datetime import datetime
from core.models import Profile, Entry, Category, Statistics, QueryFilters

class TestModels:
    def test_profile_model(self):
        """Test Profile model"""
        now = datetime.now()
        profile = Profile(id=1, name="Test", description="Desc", created_at=now)
        
        assert profile.id == 1
        assert profile.name == "Test"
        
        data = profile.to_dict()
        assert data["id"] == 1
        assert data["name"] == "Test"
        assert data["created_at"] == now.isoformat()

    def test_entry_model(self):
        """Test Entry model"""
        entry = Entry(
            id=1, profile_id=1, date=None, type="支出", 
            amount=100.0, category="Food"
        )
        
        assert entry.amount == 100.0
        assert entry.type == "支出"
        
        data = entry.to_dict()
        assert data["amount"] == 100.0
        assert data["date"] is None

    def test_category_model(self):
        """Test Category model"""
        cat = Category(id=1, name="Food", parent="Life")
        
        assert cat.name == "Food"
        assert cat.parent == "Life"
        
        data = cat.to_dict()
        assert data["name"] == "Food"
        assert data["parent"] == "Life"

    def test_statistics_model(self):
        """Test Statistics model"""
        stats = Statistics(total_income=100, total_expense=50, balance=50, count=2)
        
        assert stats.balance == 50
        
        data = stats.to_dict()
        assert data["balance"] == 50
        assert data["count"] == 2

    def test_query_filters_model(self):
        """Test QueryFilters model"""
        filters = QueryFilters(entry_type="支出", category="Food")
        
        assert filters.entry_type == "支出"
        
        data = filters.to_dict()
        assert data["entry_type"] == "支出"
        assert data["start_date"] is None
