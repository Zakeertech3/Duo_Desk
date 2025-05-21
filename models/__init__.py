from pymongo import MongoClient
from flask import current_app, g

# Database connection
def init_db(app):
    """Initialize database connection."""
    # Create MongoDB client
    mongo_client = MongoClient(app.config['MONGO_URI'])
    db = mongo_client.get_database()
    
    # Create indexes if they don't exist
    db.users.create_index("email", unique=True)
    db.queries.create_index("created_at")
    db.resources.create_index("created_at")
    
    # Make db globally accessible
    app.extensions['mongodb'] = db
    
    return db

def get_db():
    """Get database instance."""
    if 'mongodb' in current_app.extensions:
        return current_app.extensions['mongodb']
    else:
        raise RuntimeError("Database not initialized. Make sure to call init_db() first.")