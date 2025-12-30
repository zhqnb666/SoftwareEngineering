import pytest
from core.profile_manager import ProfileManager

class TestProfileManager:
    def test_create_profile_success(self, profile_manager):
        """Test creating a profile successfully"""
        profile = profile_manager.create_profile("New User", "Description")
        
        assert profile.id is not None
        assert profile.name == "New User"
        assert profile.description == "Description"
        assert profile.created_at is not None

    def test_create_profile_duplicate(self, profile_manager):
        """Test creating a duplicate profile"""
        profile_manager.create_profile("User A")
        
        with pytest.raises(ValueError, match="已存在"):
            profile_manager.create_profile("User A")

    def test_get_profile_success(self, profile_manager):
        """Test getting a profile by ID"""
        created = profile_manager.create_profile("User B")
        fetched = profile_manager.get_profile(created.id)
        
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "User B"

    def test_get_profile_not_found(self, profile_manager):
        """Test getting a non-existent profile"""
        assert profile_manager.get_profile(999) is None

    def test_get_profile_by_name(self, profile_manager):
        """Test getting a profile by name"""
        profile_manager.create_profile("User C")
        
        fetched = profile_manager.get_profile_by_name("User C")
        assert fetched is not None
        assert fetched.name == "User C"
        
        assert profile_manager.get_profile_by_name("Non Existent") is None

    def test_list_profiles(self, profile_manager):
        """Test listing all profiles"""
        assert len(profile_manager.list_profiles()) == 0
        
        profile_manager.create_profile("User 1")
        profile_manager.create_profile("User 2")
        
        profiles = profile_manager.list_profiles()
        assert len(profiles) == 2
        assert profiles[0].name == "User 1"
        assert profiles[1].name == "User 2"

    def test_update_profile_success(self, profile_manager):
        """Test updating a profile"""
        profile = profile_manager.create_profile("Old Name", "Old Desc")
        
        success = profile_manager.update_profile(
            profile.id, name="New Name", description="New Desc"
        )
        
        assert success is True
        updated = profile_manager.get_profile(profile.id)
        assert updated.name == "New Name"
        assert updated.description == "New Desc"

    def test_update_profile_duplicate_name(self, profile_manager):
        """Test updating profile name to an existing name"""
        p1 = profile_manager.create_profile("User 1")
        p2 = profile_manager.create_profile("User 2")
        
        # Should return False because exception is caught
        assert profile_manager.update_profile(p2.id, name="User 1") is False

    def test_delete_profile(self, profile_manager):
        """Test deleting a profile"""
        profile = profile_manager.create_profile("To Delete")
        
        assert profile_manager.delete_profile(profile.id) is True
        assert profile_manager.get_profile(profile.id) is None

    def test_get_profile_count(self, profile_manager):
        """Test getting profile count"""
        assert profile_manager.get_profile_count() == 0
        profile_manager.create_profile("User 1")
        assert profile_manager.get_profile_count() == 1

    def test_create_profile_db_error(self, profile_manager, monkeypatch):
        """Test database error during profile creation"""
        def mock_execute(*args, **kwargs):
            raise Exception("DB Error")
            
        monkeypatch.setattr(profile_manager.db, "execute", mock_execute)
        
        with pytest.raises(RuntimeError, match="创建账户失败"):
            profile_manager.create_profile("Error User")
