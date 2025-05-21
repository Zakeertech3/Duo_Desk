import os
from datetime import datetime
from bson.objectid import ObjectId
from models import get_db
import logging

# Set up logger
logger = logging.getLogger(__name__)

class Resource:
    """Resource model."""
    
    RESOURCE_TYPES = ['link', 'file', 'note', 'code']
    
    def __init__(self, title, content, resource_type, user_id, 
                 tags=None, file_path=None, id=None, created_at=None):
        self.title = title
        self.content = content
        self.resource_type = resource_type
        self.user_id = user_id
        self.tags = tags or []
        self.file_path = file_path
        self.id = str(id) if id else None
        self.created_at = created_at or datetime.utcnow()
        self.is_bookmarked = False
    
    def save(self):
        """Save resource to database."""
        db = get_db()
        if not self.id:
            resource_data = {
                'title': self.title,
                'content': self.content,
                'resource_type': self.resource_type,
                'user_id': self.user_id,
                'tags': self.tags,
                'file_path': self.file_path,
                'created_at': self.created_at,
                'is_bookmarked': False
            }
            result = db.resources.insert_one(resource_data)
            self.id = str(result.inserted_id)
        else:
            db.resources.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': {
                    'title': self.title,
                    'content': self.content,
                    'resource_type': self.resource_type,
                    'tags': self.tags,
                    'file_path': self.file_path
                }}
            )
        return self
    
    def toggle_bookmark(self):
        """Toggle bookmark status of resource."""
        db = get_db()
        resource_data = db.resources.find_one({'_id': ObjectId(self.id)})
        is_bookmarked = not resource_data.get('is_bookmarked', False)
        
        db.resources.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {'is_bookmarked': is_bookmarked}}
        )
        
        self.is_bookmarked = is_bookmarked
        return is_bookmarked
    
    @classmethod
    def delete(cls, resource_id):
        """Delete resource by ID."""
        try:
            db = get_db()
            resource = cls.get_by_id(resource_id)
            
            # If resource has a file, delete it
            if resource and resource.file_path:
                file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                        'static', resource.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            result = db.resources.delete_one({'_id': ObjectId(resource_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting resource {resource_id}: {str(e)}")
            raise Exception(f"Failed to delete resource: {str(e)}")
    
    @classmethod
    def get_by_id(cls, resource_id):
        """Get resource by ID."""
        db = get_db()
        resource_data = db.resources.find_one({'_id': ObjectId(resource_id)})
        if resource_data:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            return resource
        return None
    
    @classmethod
    def get_all(cls, limit=None, skip=0, sort_by='created_at', sort_dir=-1):
        """Get all resources."""
        db = get_db()
        resources = []
        
        cursor = db.resources.find().sort(sort_by, sort_dir).skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources
    
    @classmethod
    def get_all_paginated(cls, page=1, per_page=10, sort_by='created_at', sort_dir=-1):
        """Get paginated resources."""
        db = get_db()
        skip = (page - 1) * per_page
        
        # Get total count
        total = db.resources.count_documents({})
        
        # Get resources for current page
        resources = cls.get_all(limit=per_page, skip=skip, sort_by=sort_by, sort_dir=sort_dir)
        
        return resources, total
    
    @classmethod
    def get_by_type(cls, resource_type, limit=None):
        """Get resources by type."""
        db = get_db()
        resources = []
        
        cursor = db.resources.find({'resource_type': resource_type}).sort('created_at', -1)
        if limit:
            cursor = cursor.limit(limit)
            
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources
    
    @classmethod
    def get_by_type_paginated(cls, resource_type, page=1, per_page=10):
        """Get paginated resources by type."""
        db = get_db()
        skip = (page - 1) * per_page
        
        # Get total count
        total = db.resources.count_documents({'resource_type': resource_type})
        
        # Get resources for current page
        cursor = db.resources.find({'resource_type': resource_type}).sort('created_at', -1).skip(skip).limit(per_page)
        
        resources = []
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources, total
    
    @classmethod
    def get_by_tag(cls, tag, limit=None):
        """Get resources by tag."""
        db = get_db()
        resources = []
        
        cursor = db.resources.find({'tags': tag}).sort('created_at', -1)
        if limit:
            cursor = cursor.limit(limit)
            
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources
    
    @classmethod
    def get_by_tag_paginated(cls, tag, page=1, per_page=10):
        """Get paginated resources by tag."""
        db = get_db()
        skip = (page - 1) * per_page
        
        # Get total count
        total = db.resources.count_documents({'tags': tag})
        
        # Get resources for current page
        cursor = db.resources.find({'tags': tag}).sort('created_at', -1).skip(skip).limit(per_page)
        
        resources = []
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources, total
    
    @classmethod
    def get_by_tags(cls, tags, limit=None, exclude_id=None):
        """Get resources that match any of the given tags."""
        db = get_db()
        resources = []
        
        query = {'tags': {'$in': tags}}
        if exclude_id:
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        
        cursor = db.resources.find(query).sort('created_at', -1)
        if limit:
            cursor = cursor.limit(limit)
            
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources
    
    @classmethod
    def get_bookmarked(cls, limit=None):
        """Get bookmarked resources."""
        db = get_db()
        resources = []
        
        cursor = db.resources.find({'is_bookmarked': True}).sort('created_at', -1)
        if limit:
            cursor = cursor.limit(limit)
            
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', True)
            resources.append(resource)
        
        return resources
    
    @classmethod
    def search(cls, query, limit=None):
        """Search resources by title and content."""
        db = get_db()
        resources = []
        
        cursor = db.resources.find({
            '$or': [
                {'title': {'$regex': query, '$options': 'i'}},
                {'content': {'$regex': query, '$options': 'i'}},
                {'tags': {'$regex': query, '$options': 'i'}}
            ]
        }).sort('created_at', -1)
        
        if limit:
            cursor = cursor.limit(limit)
            
        for resource_data in cursor:
            resource = cls(
                title=resource_data['title'],
                content=resource_data['content'],
                resource_type=resource_data['resource_type'],
                user_id=resource_data['user_id'],
                tags=resource_data.get('tags', []),
                file_path=resource_data.get('file_path'),
                id=resource_data['_id'],
                created_at=resource_data.get('created_at')
            )
            resource.is_bookmarked = resource_data.get('is_bookmarked', False)
            resources.append(resource)
        
        return resources
    
    @classmethod
    def count_by_type(cls):
        """Count resources by type."""
        db = get_db()
        return {
            resource_type: db.resources.count_documents({'resource_type': resource_type})
            for resource_type in cls.RESOURCE_TYPES
        }
    
    def to_dict(self):
        """Convert resource to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'resource_type': self.resource_type,
            'user_id': self.user_id,
            'tags': self.tags,
            'file_path': self.file_path,
            'created_at': self.created_at,
            'is_bookmarked': self.is_bookmarked
        }