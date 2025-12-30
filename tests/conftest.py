import pytest
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Database
from core.category_manager import CategoryManager
from core.entry_manager import EntryManager
from core.profile_manager import ProfileManager

@pytest.fixture
def db():
    """Create a temporary in-memory database for testing"""
    database = Database(":memory:")
    database.init_db()
    yield database
    if database.conn:
        database.conn.close()

@pytest.fixture
def category_manager(db):
    """Create a CategoryManager instance"""
    return CategoryManager(db)

@pytest.fixture
def entry_manager(db):
    """Create an EntryManager instance"""
    return EntryManager(db)

@pytest.fixture
def profile_manager(db):
    """Create a ProfileManager instance"""
    return ProfileManager(db)
