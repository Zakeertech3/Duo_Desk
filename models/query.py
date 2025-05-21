from datetime import datetime
from bson.objectid import ObjectId
from models import get_db
import logging

# Set up logger
logger = logging.getLogger(__name__)

class Query:
    """Query model."""
    
    PRIORITY_LEVELS = ['low', 'medium', 'high']
    STATUS_OPTIONS = ['pending', 'in_progress', 'resolved']
    
    def __init__(self, title, content, priority, user_id, status='pending', 
                 id=None, created_at=None, updated_at=None, responses=None):
        self.title = title
        self.content = content
        self.priority = priority
        self.user_id = str(user_id)  # Convert to string for consistency
        self.status = status
        self.id = str(id) if id else None
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or self.created_at
        self.responses = responses or []
    
    def save(self):
        """Save query to database."""
        try:
            db = get_db()
            self.updated_at = datetime.utcnow()
            
            if not self.id:
                query_data = {
                    'title': self.title,
                    'content': self.content,
                    'priority': self.priority,
                    'user_id': self.user_id,
                    'status': self.status,
                    'created_at': self.created_at,
                    'updated_at': self.updated_at,
                    'responses': self.responses
                }
                result = db.queries.insert_one(query_data)
                self.id = str(result.inserted_id)
                logger.info(f"Created new query with ID: {self.id}")
            else:
                result = db.queries.update_one(
                    {'_id': ObjectId(self.id)},
                    {'$set': {
                        'title': self.title,
                        'content': self.content,
                        'priority': self.priority,
                        'status': self.status,
                        'updated_at': self.updated_at,
                        'responses': self.responses
                    }}
                )
                if result.modified_count == 0:
                    logger.warning(f"No document was updated for query ID: {self.id}")
                
            return self
        except Exception as e:
            logger.error(f"Error saving query: {str(e)}")
            raise Exception(f"Failed to save query: {str(e)}")
    
    def add_response(self, content, user_id):
        """Add response to query."""
        try:
            db = get_db()
            
            # Ensure user_id is a string for consistency
            user_id = str(user_id)
            
            # Create response object
            response = {
                'content': content,
                'user_id': user_id,
                'created_at': datetime.utcnow()
            }
            
            # Add to responses list
            if not hasattr(self, 'responses') or self.responses is None:
                self.responses = []
            
            self.responses.append(response)
            self.updated_at = response['created_at']
            
            # Log what we're trying to do
            logger.info(f"Adding response to query {self.id} from user {user_id}")
            
            # Update in database
            result = db.queries.update_one(
                {'_id': ObjectId(self.id)},
                {
                    '$push': {'responses': response},
                    '$set': {'updated_at': self.updated_at}
                }
            )
            
            # Check if the update was successful
            if result.modified_count == 0:
                logger.warning(f"No document was updated for query ID: {self.id}")
                raise Exception("No document was updated. The query might not exist.")
                
            logger.info(f"Successfully added response to query {self.id}")
            return self
            
        except Exception as e:
            logger.error(f"Error adding response to query {self.id}: {str(e)}")
            # Re-raise the exception with additional context
            raise Exception(f"Failed to add response: {str(e)}")
    
    def update_status(self, status):
        """Update query status."""
        try:
            db = get_db()
            
            if status in self.STATUS_OPTIONS:
                self.status = status
                self.updated_at = datetime.utcnow()
                
                result = db.queries.update_one(
                    {'_id': ObjectId(self.id)},
                    {'$set': {
                        'status': self.status,
                        'updated_at': self.updated_at
                    }}
                )
                
                if result.modified_count == 0:
                    logger.warning(f"No document was updated for query ID: {self.id}")
            else:
                raise ValueError(f"Invalid status: {status}. Must be one of {self.STATUS_OPTIONS}")
            
            return self
        except Exception as e:
            logger.error(f"Error updating status for query {self.id}: {str(e)}")
            raise Exception(f"Failed to update status: {str(e)}")
    
    @classmethod
    def get_by_id(cls, query_id):
        """Get query by ID."""
        try:
            db = get_db()
            query_data = db.queries.find_one({'_id': ObjectId(query_id)})
            if query_data:
                return cls(
                    title=query_data['title'],
                    content=query_data['content'],
                    priority=query_data['priority'],
                    user_id=query_data['user_id'],
                    status=query_data['status'],
                    id=query_data['_id'],
                    created_at=query_data.get('created_at'),
                    updated_at=query_data.get('updated_at'),
                    responses=query_data.get('responses', [])
                )
            return None
        except Exception as e:
            logger.error(f"Error getting query by ID {query_id}: {str(e)}")
            raise Exception(f"Failed to get query: {str(e)}")
    
    @classmethod
    def get_all(cls, limit=None, skip=0, sort_by='created_at', sort_dir=-1):
        """Get all queries."""
        try:
            db = get_db()
            queries = []
            
            cursor = db.queries.find().sort(sort_by, sort_dir).skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            for query_data in cursor:
                queries.append(cls(
                    title=query_data['title'],
                    content=query_data['content'],
                    priority=query_data['priority'],
                    user_id=query_data['user_id'],
                    status=query_data['status'],
                    id=query_data['_id'],
                    created_at=query_data.get('created_at'),
                    updated_at=query_data.get('updated_at'),
                    responses=query_data.get('responses', [])
                ))
            
            return queries
        except Exception as e:
            logger.error(f"Error getting all queries: {str(e)}")
            return []
    
    @classmethod
    def get_by_status(cls, status, limit=None):
        """Get queries by status."""
        try:
            if status not in cls.STATUS_OPTIONS:
                logger.warning(f"Invalid status filter: {status}")
                return []
                
            db = get_db()
            queries = []
            
            cursor = db.queries.find({'status': status}).sort('created_at', -1)
            if limit:
                cursor = cursor.limit(limit)
                
            for query_data in cursor:
                queries.append(cls(
                    title=query_data['title'],
                    content=query_data['content'],
                    priority=query_data['priority'],
                    user_id=query_data['user_id'],
                    status=query_data['status'],
                    id=query_data['_id'],
                    created_at=query_data.get('created_at'),
                    updated_at=query_data.get('updated_at'),
                    responses=query_data.get('responses', [])
                ))
            
            return queries
        except Exception as e:
            logger.error(f"Error getting queries by status {status}: {str(e)}")
            return []
    
    @classmethod
    def get_by_priority(cls, priority, limit=None):
        """Get queries by priority."""
        try:
            if priority not in cls.PRIORITY_LEVELS:
                logger.warning(f"Invalid priority filter: {priority}")
                return []
                
            db = get_db()
            queries = []
            
            cursor = db.queries.find({'priority': priority}).sort('created_at', -1)
            if limit:
                cursor = cursor.limit(limit)
                
            for query_data in cursor:
                queries.append(cls(
                    title=query_data['title'],
                    content=query_data['content'],
                    priority=query_data['priority'],
                    user_id=query_data['user_id'],
                    status=query_data['status'],
                    id=query_data['_id'],
                    created_at=query_data.get('created_at'),
                    updated_at=query_data.get('updated_at'),
                    responses=query_data.get('responses', [])
                ))
            
            return queries
        except Exception as e:
            logger.error(f"Error getting queries by priority {priority}: {str(e)}")
            return []
    
    @classmethod
    def count_by_status(cls):
        """Count queries by status."""
        try:
            db = get_db()
            return {
                status: db.queries.count_documents({'status': status})
                for status in cls.STATUS_OPTIONS
            }
        except Exception as e:
            logger.error(f"Error counting queries by status: {str(e)}")
            return {status: 0 for status in cls.STATUS_OPTIONS}
    
    @classmethod
    def count_by_priority(cls):
        """Count queries by priority."""
        try:
            db = get_db()
            return {
                priority: db.queries.count_documents({'priority': priority})
                for priority in cls.PRIORITY_LEVELS
            }
        except Exception as e:
            logger.error(f"Error counting queries by priority: {str(e)}")
            return {priority: 0 for priority in cls.PRIORITY_LEVELS}
    
    def to_dict(self):
        """Convert query to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'priority': self.priority,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'responses': self.responses
        }