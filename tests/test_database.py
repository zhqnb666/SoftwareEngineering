import pytest
import sqlite3
from unittest.mock import MagicMock, patch
from core.database import Database

class TestDatabase:
    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test.db")

    @pytest.fixture
    def db(self, db_path):
        db = Database(db_path)
        db.init_db()
        yield db
        db.close()

    def test_init_connection(self, db_path):
        """Test database connection initialization"""
        db = Database(db_path)
        assert db.conn is not None
        db.close()
        assert db.conn is None

    def test_init_db_success(self, db):
        """Test database table initialization"""
        # Check if tables exist
        tables = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t['name'] for t in tables]
        assert "profiles" in table_names
        assert "categories" in table_names
        assert "entries" in table_names

    def test_execute_success(self, db):
        """Test successful execution"""
        # Insert
        row_id = db.execute(
            "INSERT INTO profiles (name) VALUES (?)", ("Test User",)
        )
        assert row_id > 0
        
        # Update
        count = db.execute(
            "UPDATE profiles SET description = ? WHERE id = ?", ("Desc", row_id)
        )
        assert count == 1

    def test_execute_error(self, db):
        """Test execution error"""
        with pytest.raises(Exception):
            db.execute("SELECT * FROM non_existent_table")

    def test_fetchall_success(self, db):
        """Test fetchall success"""
        db.execute("INSERT INTO profiles (name) VALUES (?)", ("User 1",))
        db.execute("INSERT INTO profiles (name) VALUES (?)", ("User 2",))
        
        results = db.fetchall("SELECT * FROM profiles")
        assert len(results) >= 2

    def test_fetchall_error(self, db, monkeypatch):
        """Test fetchall error"""
        # Mock cursor to raise exception
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Fetch Error")
        mock_conn.cursor.return_value = mock_cursor
        
        # Replace the connection in the db object
        db.conn = mock_conn
        
        with pytest.raises(Exception) as excinfo:
            db.fetchall("SELECT * FROM profiles")
        assert "Fetch Error" in str(excinfo.value)

    def test_fetchone_success(self, db):
        """Test fetchone success"""
        db.execute("INSERT INTO profiles (name) VALUES (?)", ("User 1",))
        
        result = db.fetchone("SELECT * FROM profiles WHERE name = ?", ("User 1",))
        assert result is not None
        assert result['name'] == "User 1"
        
        result = db.fetchone("SELECT * FROM profiles WHERE name = ?", ("Non Existent",))
        assert result is None

    def test_fetchone_error(self, db, monkeypatch):
        """Test fetchone error"""
        # Mock cursor to raise exception
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Fetch Error")
        mock_conn.cursor.return_value = mock_cursor
        
        # Replace the connection in the db object
        db.conn = mock_conn
        
        with pytest.raises(Exception) as excinfo:
            db.fetchone("SELECT * FROM profiles")
        assert "Fetch Error" in str(excinfo.value)

    def test_transaction(self, db):
        """Test transaction operations"""
        db.begin_transaction()
        db.execute("INSERT INTO profiles (name) VALUES (?)", ("Trans User",))
        db.rollback()
        
        result = db.fetchone("SELECT * FROM profiles WHERE name = ?", ("Trans User",))
        assert result is None
        
        db.begin_transaction()
        db.execute("INSERT INTO profiles (name) VALUES (?)", ("Trans User 2",))
        db.commit()
        
        result = db.fetchone("SELECT * FROM profiles WHERE name = ?", ("Trans User 2",))
        assert result is not None

    def test_connection_error(self, monkeypatch):
        """Test connection error"""
        def mock_connect(*args, **kwargs):
            raise Exception("Connection Error")
            
        monkeypatch.setattr(sqlite3, "connect", mock_connect)
        
        with pytest.raises(Exception) as excinfo:
            Database(":memory:")
        assert "Connection Error" in str(excinfo.value)

    def test_init_db_error(self, db_path, monkeypatch):
        """Test init_db error"""
        # We need to mock execute to raise exception during init_db
        # But init_db calls execute multiple times.
        
        db = Database(db_path)
        
        def mock_execute(*args, **kwargs):
            raise Exception("Init Error")
            
        monkeypatch.setattr(db, "execute", mock_execute)
        
        # init_db catches exception and prints it, doesn't raise
        # We can check if it calls rollback
        db.rollback = MagicMock()

        with pytest.raises(Exception, match="Init Error"):
            db.init_db()

        db.rollback.assert_called_once()
        db.close()

    def test_not_connected_error(self, db_path):
        """Test operations when not connected"""
        db = Database(db_path)
        db.close()
        
        with pytest.raises(RuntimeError):
            db.execute("SELECT 1")
            
        with pytest.raises(RuntimeError):
            db.fetchall("SELECT 1")
            
        with pytest.raises(RuntimeError):
            db.fetchone("SELECT 1")
            
        with pytest.raises(RuntimeError):
            db.begin_transaction()
