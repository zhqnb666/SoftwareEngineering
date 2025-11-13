"""
账户管理模块
提供账户的增删查功能
"""
from typing import List, Optional
from datetime import datetime
import logging

from .database import Database
from .models import Profile


class ProfileManager:
    """账户管理器"""
    
    def __init__(self, db: Database):
        """初始化账户管理器
        
        Args:
            db: 数据库连接实例
        """
        self.db = db
    
    def create_profile(self, name: str, description: str = "") -> Profile:
        """创建新账户
        
        Args:
            name: 账户名称
            description: 账户描述
            
        Returns:
            新创建的账户对象
            
        Raises:
            ValueError: 账户名已存在
        """
        # 检查账户名是否已存在
        if self.get_profile_by_name(name):
            raise ValueError(f"账户名 '{name}' 已存在")
        
        try:
            # 插入新账户
            profile_id = self.db.execute(
                "INSERT INTO profiles (name, description, created_at) VALUES (?, ?, ?)",
                (name, description, datetime.now())
            )
            
            self.db.commit()
            
            # 返回新创建的账户
            return self.get_profile(profile_id)
            
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"创建账户失败: {e}")
    
    def get_profile(self, profile_id: int) -> Optional[Profile]:
        """根据 ID 获取账户
        
        Args:
            profile_id: 账户 ID
            
        Returns:
            账户对象或 None
        """
        row = self.db.fetchone(
            "SELECT * FROM profiles WHERE id = ?",
            (profile_id,)
        )
        
        if row:
            return Profile(
                id=row['id'],
                name=row['name'],
                description=row['description'] or "",
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
        return None
    
    def get_profile_by_name(self, name: str) -> Optional[Profile]:
        """根据名称获取账户
        
        Args:
            name: 账户名称
            
        Returns:
            账户对象或 None
        """
        row = self.db.fetchone(
            "SELECT * FROM profiles WHERE name = ?",
            (name,)
        )
        
        if row:
            return Profile(
                id=row['id'],
                name=row['name'],
                description=row['description'] or "",
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
        return None
    
    def list_profiles(self) -> List[Profile]:
        """获取所有账户列表
        
        Returns:
            账户列表，按创建时间排序
        """
        rows = self.db.fetchall(
            "SELECT * FROM profiles ORDER BY created_at ASC"
        )
        
        profiles = []
        for row in rows:
            profiles.append(Profile(
                id=row['id'],
                name=row['name'],
                description=row['description'] or "",
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            ))
        
        return profiles
    
    def delete_profile(self, profile_id: int) -> bool:
        """删除账户
        
        Args:
            profile_id: 账户 ID
            
        Returns:
            删除是否成功
        """
        try:
            # 由于设置了 ON DELETE CASCADE，删除账户会自动删除关联的条目
            rows_affected = self.db.execute(
                "DELETE FROM profiles WHERE id = ?",
                (profile_id,)
            )
            
            self.db.commit()
            
            return rows_affected > 0
            
        except Exception as e:
            self.db.rollback()
            logging.getLogger(__name__).exception("删除账户失败: %s", e)
            return False
    
    def update_profile(self, profile_id: int, name: str = None, description: str = None) -> bool:
        """更新账户信息
        
        Args:
            profile_id: 账户 ID
            name: 新的账户名称（可选）
            description: 新的账户描述（可选）
            
        Returns:
            更新是否成功
        """
        if not name and description is None:
            return True  # 没有要更新的内容
        
        try:
            # 检查新名称是否已存在（如果提供了新名称）
            if name:
                existing_profile = self.get_profile_by_name(name)
                if existing_profile and existing_profile.id != profile_id:
                    raise ValueError(f"账户名 '{name}' 已存在")
            
            # 构建更新语句
            update_fields = []
            params = []
            
            if name:
                update_fields.append("name = ?")
                params.append(name)
            
            if description is not None:
                update_fields.append("description = ?")
                params.append(description)
            
            params.append(profile_id)
            
            sql = f"UPDATE profiles SET {', '.join(update_fields)} WHERE id = ?"
            
            rows_affected = self.db.execute(sql, tuple(params))
            self.db.commit()
            
            return rows_affected > 0
            
        except Exception as e:
            self.db.rollback()
            logging.getLogger(__name__).exception("更新账户失败: %s", e)
            return False
    
    def get_profile_count(self) -> int:
        """获取账户总数
        
        Returns:
            账户总数
        """
        row = self.db.fetchone("SELECT COUNT(*) as count FROM profiles")
        return row['count'] if row else 0