from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime
from models import get_db

class User(UserMixin):
    """User model."""
    
    def __init__(self, email, name, password=None, id=None, created_at=None):
        self.email = email
        self.name = name
        self.password_hash = generate_password_hash(password) if password else None
        self.id = str(id) if id else None
        self.created_at = created_at or datetime.utcnow()
    
    def check_password(self, password):
        """Check if password matches."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def save(self):
        """Save user to database."""
        db = get_db()
        
        if not self.id:
            user_data = {
                'email': self.email,
                'name': self.name,
                'password_hash': self.password_hash,
                'created_at': self.created_at
            }
            result = db.users.insert_one(user_data)
            self.id = str(result.inserted_id)
        else:
            db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {
                    'email': self.email,
                    'name': self.name,
                    'password_hash': self.password_hash
                }}
            )
        return self
    
    @classmethod
    def get_by_id(cls, user_id):
        """Get user by ID."""
        db = get_db()
        user_data = db.users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            user = cls(
                email=user_data['email'],
                name=user_data['name'],
                id=user_data['_id'],
                created_at=user_data.get('created_at')
            )
            user.password_hash = user_data.get('password_hash')
            return user
        return None
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email."""
        db = get_db()
        user_data = db.users.find_one({'email': email})
        if user_data:
            user = cls(
                email=user_data['email'],
                name=user_data['name'],
                id=user_data['_id'],
                created_at=user_data.get('created_at')
            )
            user.password_hash = user_data.get('password_hash')
            return user
        return None
    
    @classmethod
    def get_all_users(cls):
        """Get all users."""
        db = get_db()
        users = []
        for user_data in db.users.find():
            user = cls(
                email=user_data['email'],
                name=user_data['name'],
                id=user_data['_id'],
                created_at=user_data.get('created_at')
            )
            user.password_hash = user_data.get('password_hash')
            users.append(user)
        return users
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at
        }