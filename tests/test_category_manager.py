import pytest
from core.models import Category

class TestCategoryManager:
    def test_init_default_categories(self, category_manager):
        """Test initialization of default categories"""
        category_manager.init_default_categories()
        
        # Check some default categories
        income_cats = category_manager.get_categories_by_type("收入")
        assert "工资" in income_cats
        assert "奖金" in income_cats
        
        expense_cats = category_manager.get_categories_by_type("支出")
        assert "餐饮" in expense_cats
        assert "交通" in expense_cats
        
        # Check subcategories
        assert "早餐" in expense_cats["餐饮"]
        assert "地铁" in expense_cats["交通"]

    def test_add_category_success(self, category_manager):
        """Test adding a new category successfully"""
        cat = category_manager.add_category("测试分类")
        assert cat.name == "测试分类"
        assert cat.parent is None
        assert cat.id is not None
        
        # Verify it's in the database
        fetched = category_manager.get_category_by_name("测试分类")
        assert fetched is not None
        assert fetched.name == "测试分类"

    def test_add_subcategory_success(self, category_manager):
        """Test adding a subcategory successfully"""
        parent = category_manager.add_category("父分类")
        sub = category_manager.add_category("子分类", parent="父分类")
        
        assert sub.name == "子分类"
        assert sub.parent == "父分类"
        
        # Verify relationship
        subs = category_manager.get_categories(parent="父分类")
        assert len(subs) == 1
        assert subs[0].name == "子分类"

    def test_add_category_duplicate(self, category_manager):
        """Test adding a duplicate category raises ValueError"""
        category_manager.add_category("重复分类")
        
        with pytest.raises(ValueError, match="已存在"):
            category_manager.add_category("重复分类")

    def test_get_categories_top_level(self, category_manager):
        """Test getting top-level categories"""
        category_manager.add_category("分类1")
        category_manager.add_category("分类2")
        category_manager.add_category("子分类", parent="分类1")
        
        top_level = category_manager.get_categories(parent=None)
        names = [c.name for c in top_level]
        
        assert "分类1" in names
        assert "分类2" in names
        assert "子分类" not in names

    def test_get_all_categories(self, category_manager):
        """Test getting all categories"""
        category_manager.add_category("A")
        category_manager.add_category("B", parent="A")
        
        all_cats = category_manager.get_all_categories()
        assert len(all_cats) == 2
        names = [c.name for c in all_cats]
        assert "A" in names
        assert "B" in names

    def test_delete_category_success(self, category_manager):
        """Test deleting a category"""
        cat = category_manager.add_category("要删除的分类")
        assert category_manager.get_category_by_name("要删除的分类") is not None
        
        result = category_manager.delete_category(cat.id)
        assert result is True
        assert category_manager.get_category_by_name("要删除的分类") is None

    def test_delete_category_fail(self, category_manager):
        """Test deleting a non-existent category"""
        result = category_manager.delete_category(99999)
        assert result is False

    def test_get_category_by_name_not_found(self, category_manager):
        """Test getting a non-existent category by name"""
        cat = category_manager.get_category_by_name("不存在")
        assert cat is None

    def test_get_categories_by_type_structure(self, category_manager):
        """Test the structure returned by get_categories_by_type"""
        # Need to init defaults first to have the structure
        category_manager.init_default_categories()
        
        structure = category_manager.get_categories_by_type("支出")
        assert isinstance(structure, dict)
        assert "餐饮" in structure
        assert isinstance(structure["餐饮"], list)
        assert "早餐" in structure["餐饮"]

    def test_add_category_error(self, category_manager, monkeypatch):
        """Test error handling during category addition"""
        def mock_execute(*args, **kwargs):
            raise Exception("Database error")
            
        monkeypatch.setattr(category_manager.db, "execute", mock_execute)
        
        with pytest.raises(RuntimeError, match="添加分类失败"):
            category_manager.add_category("ErrorCat")
