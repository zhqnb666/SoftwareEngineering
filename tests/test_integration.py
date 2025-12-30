import pytest
from datetime import date
from core.models import QueryFilters

class TestIntegration:
    """Integration tests for the Accounting Book application"""

    def test_workflow_category_entry_stats(self, category_manager, entry_manager, profile_manager):
        """
        Integration Test Group 1: Business Logic Workflow
        Tests the interaction between CategoryManager, EntryManager and ProfileManager.
        Flow:
        1. Create Profile
        2. Create Categories
        3. Add Entries using those categories
        4. Verify Statistics
        """
        # 1. Create Profile
        profile = profile_manager.create_profile("User1")
        
        # 2. Create Categories
        # Create "Work" -> "Salary"
        work_cat = category_manager.add_category("Work")
        category_manager.add_category("Salary", parent="Work")
        
        # Create "Life" -> "Food"
        life_cat = category_manager.add_category("Life")
        category_manager.add_category("Food", parent="Life")
        
        # 3. Add Entries
        # Income: 5000
        entry_manager.add_entry(
            profile.id, date.today(), "收入", 5000.0, "Work", "Salary"
        )
        
        # Expense: 50 + 100
        entry_manager.add_entry(
            profile.id, date.today(), "支出", 50.0, "Life", "Food"
        )
        entry_manager.add_entry(
            profile.id, date.today(), "支出", 100.0, "Life", "Food"
        )
        
        # 4. Verify Statistics
        stats = entry_manager.get_statistics(profile.id)
        
        assert stats.total_income == 5000.0
        assert stats.total_expense == 150.0
        assert stats.balance == 4850.0
        assert stats.count == 3
        
        # Verify Filtering by Category
        filters = QueryFilters(category="Life")
        entries = entry_manager.get_entries(profile.id, filters)
        assert len(entries) == 2
        assert all(e.category == "Life" for e in entries)

    def test_isolation_profiles(self, profile_manager, entry_manager):
        """
        Integration Test Group 2: Data Isolation
        Tests that data is properly isolated between different profiles.
        Flow:
        1. Create two profiles (Alice, Bob)
        2. Add entries for both
        3. Verify Alice sees only her entries
        4. Verify Bob sees only his entries
        5. Verify deletion of Alice removes her entries but keeps Bob's
        """
        # 1. Create Profiles
        alice = profile_manager.create_profile("Alice")
        bob = profile_manager.create_profile("Bob")
        
        # 2. Add Entries
        # Alice: 100
        entry_manager.add_entry(
            alice.id, date.today(), "支出", 100.0, "Food"
        )
        
        # Bob: 200, 300
        entry_manager.add_entry(
            bob.id, date.today(), "支出", 200.0, "Food"
        )
        entry_manager.add_entry(
            bob.id, date.today(), "收入", 300.0, "Salary"
        )
        
        # 3. Verify Alice's View
        alice_entries = entry_manager.get_entries(alice.id)
        assert len(alice_entries) == 1
        assert alice_entries[0].amount == 100.0
        
        alice_stats = entry_manager.get_statistics(alice.id)
        assert alice_stats.total_expense == 100.0
        
        # 4. Verify Bob's View
        bob_entries = entry_manager.get_entries(bob.id)
        assert len(bob_entries) == 2
        
        bob_stats = entry_manager.get_statistics(bob.id)
        assert bob_stats.total_expense == 200.0
        assert bob_stats.total_income == 300.0
        
        # 5. Verify Deletion Cascade
        profile_manager.delete_profile(alice.id)
        
        # Alice's entries should be gone
        assert entry_manager.get_entry_count(alice.id) == 0
        
        # Bob's entries should remain
        assert entry_manager.get_entry_count(bob.id) == 2
        bob_entries_after = entry_manager.get_entries(bob.id)
        assert len(bob_entries_after) == 2
