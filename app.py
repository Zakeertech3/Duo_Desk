import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from werkzeug.utils import secure_filename
from datetime import datetime

# Import configuration
from config import get_config

# Create Flask application
app = Flask(__name__)
app.config.from_object(get_config())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize Flask-Mail
mail = Mail(app)

# Initialize database
from models import init_db
db = init_db(app)

# After database is initialized, import models
from models.user import User
from models.query import Query
from models.resource import Resource

# Import utility functions
from utils.helpers import (
    allowed_file, save_file, format_datetime, nl2br,
    send_notification_email, get_priority_class, get_status_class
)

# Import email helpers
from utils.email_helpers import (
    notify_high_priority_query, notify_new_response, notify_status_update
)

# Template filters
app.jinja_env.filters['format_datetime'] = format_datetime
app.jinja_env.filters['priority_class'] = get_priority_class
app.jinja_env.filters['status_class'] = get_status_class
app.jinja_env.filters['nl2br'] = nl2br

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# Setup function for app initialization
def setup_app():
    # Ensure uploads directory exists
    uploads_dir = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Check if we have at least 2 users
    users = User.get_all_users()
    if len(users) < 2:
        # Create default users if there are fewer than 2
        if not User.get_by_email('zakeer1410@gmail.com'):
            user1 = User('zakeer1410@gmail.com', 'Zakeer', 'password123')
            user1.save()
            logger.info("Created user: zakeer1410@gmail.com")
        
        if not User.get_by_email('zakeer1408@gmail.com'):  # Updated second user email
            user2 = User('zakeer1408@gmail.com', 'Second User', 'password123')
            user2.save()
            logger.info("Created user: zakeer1408@gmail.com")

# Initialize the app with setup function
with app.app_context():
    setup_app()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.get_by_email(email)
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        flash('Invalid email or password.', 'danger')
        logger.warning(f"Failed login attempt for email: {email}")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get counts for different query statuses and priorities
        status_counts = Query.count_by_status()
        priority_counts = Query.count_by_priority()
        
        # Get recent queries
        recent_queries = Query.get_all(limit=5)
        
        # Get high priority queries
        high_priority_queries = Query.get_by_priority('high', limit=3)
        
        # Get bookmarked resources
        bookmarked_resources = Resource.get_bookmarked(limit=5)
        
        return render_template(
            'dashboard.html',
            status_counts=status_counts,
            priority_counts=priority_counts,
            recent_queries=recent_queries,
            high_priority_queries=high_priority_queries,
            bookmarked_resources=bookmarked_resources
        )
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return render_template(
            'dashboard.html', 
            status_counts={}, 
            priority_counts={}, 
            recent_queries=[], 
            high_priority_queries=[], 
            bookmarked_resources=[]
        )

# Query routes
@app.route('/queries')
@login_required
def queries_list():
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    if status_filter and status_filter in Query.STATUS_OPTIONS:
        queries = Query.get_by_status(status_filter)
    elif priority_filter and priority_filter in Query.PRIORITY_LEVELS:
        queries = Query.get_by_priority(priority_filter)
    else:
        queries = Query.get_all()
    
    return render_template(
        'queries/list.html',
        queries=queries,
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@app.route('/queries/create', methods=['GET', 'POST'])
@login_required
def create_query():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        priority = request.form.get('priority')
        
        if not title or not content or not priority:
            flash('All fields are required.', 'danger')
            return render_template(
                'queries/create.html',
                title=title,
                content=content,
                priority=priority
            )
        
        try:
            query = Query(
                title=title,
                content=content,
                priority=priority,
                user_id=current_user.id
            )
            query.save()
            
            # Send notification for high priority queries
            if priority == 'high':
                notify_high_priority_query(mail, query, current_user.id)
            
            flash('Query created successfully!', 'success')
            return redirect(url_for('query_detail', query_id=query.id))
        except Exception as e:
            logger.error(f"Error creating query: {str(e)}")
            flash(f"Error creating query: {str(e)}", 'danger')
            return render_template(
                'queries/create.html',
                title=title,
                content=content,
                priority=priority
            )
    
    return render_template('queries/create.html')

@app.route('/queries/<query_id>')
@login_required
def query_detail(query_id):
    query = Query.get_by_id(query_id)
    
    if not query:
        flash('Query not found.', 'danger')
        return redirect(url_for('queries_list'))
    
    # Get user info for the query and responses
    query_user = User.get_by_id(query.user_id)
    
    response_users = {}
    for response in query.responses:
        if response['user_id'] not in response_users:
            response_users[response['user_id']] = User.get_by_id(response['user_id'])
    
    return render_template(
        'queries/detail.html',
        query=query,
        query_user=query_user,
        response_users=response_users
    )

@app.route('/queries/<query_id>/respond', methods=['POST'])
@login_required
def respond_to_query(query_id):
    # Log information for debugging
    logger.info(f"Responding to query {query_id}")
    logger.info(f"Form data: {request.form}")
    
    query = Query.get_by_id(query_id)
    
    if not query:
        flash('Query not found.', 'danger')
        return redirect(url_for('queries_list'))
    
    content = request.form.get('content')
    
    if not content:
        flash('Response content is required.', 'danger')
        return redirect(url_for('query_detail', query_id=query.id))
    
    try:
        # Add the response
        response_data = {
            'content': content,
            'user_id': current_user.id,
            'created_at': datetime.utcnow()
        }
        query.add_response(content, current_user.id)
        
        # Send email notification
        notify_new_response(mail, query, response_data, current_user.id)
        
        flash('Response added successfully!', 'success')
    except Exception as e:
        logger.error(f"Error adding response: {str(e)}")
        flash(f'Error adding response: {str(e)}', 'danger')
    
    return redirect(url_for('query_detail', query_id=query.id))

@app.route('/queries/<query_id>/status', methods=['POST'])
@login_required
def update_query_status(query_id):
    query = Query.get_by_id(query_id)
    
    if not query:
        flash('Query not found.', 'danger')
        return redirect(url_for('queries_list'))
    
    status = request.form.get('status')
    
    if not status or status not in Query.STATUS_OPTIONS:
        flash('Invalid status.', 'danger')
        return redirect(url_for('query_detail', query_id=query.id))
    
    try:
        # Store the previous status for notification
        previous_status = query.status
        
        # Update the status
        query.update_status(status)
        
        # Send notification
        notify_status_update(mail, query, current_user.id, previous_status)
        
        flash('Status updated successfully!', 'success')
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        flash(f'Error updating status: {str(e)}', 'danger')
    
    return redirect(url_for('query_detail', query_id=query.id))

# Resource routes
@app.route('/resources')
@login_required
def resources_list():
    type_filter = request.args.get('type')
    tag_filter = request.args.get('tag')
    
    if type_filter and type_filter in Resource.RESOURCE_TYPES:
        resources = Resource.get_by_type(type_filter)
    elif tag_filter:
        resources = Resource.get_by_tag(tag_filter)
    else:
        resources = Resource.get_all()
    
    # Get all unique tags for filter dropdown
    all_resources = Resource.get_all()
    all_tags = set()
    for resource in all_resources:
        all_tags.update(resource.tags)
    
    return render_template(
        'resources/list.html',
        resources=resources,
        type_filter=type_filter,
        tag_filter=tag_filter,
        all_tags=sorted(list(all_tags))
    )

@app.route('/resources/create', methods=['GET', 'POST'])
@login_required
def create_resource():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content', '')
        resource_type = request.form.get('resource_type')
        tags = request.form.get('tags', '').split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        
        if not title or not resource_type:
            flash('Title and resource type are required.', 'danger')
            return render_template(
                'resources/create.html',
                title=title,
                content=content,
                resource_type=resource_type,
                tags=','.join(tags)
            )
        
        # Handle file upload for 'file' resource type
        file_path = None
        if resource_type == 'file' and 'file' in request.files:
            file = request.files['file']
            if file.filename:
                if allowed_file(file.filename):
                    file_path = save_file(file)
                else:
                    flash('Invalid file type.', 'danger')
                    return render_template(
                        'resources/create.html',
                        title=title,
                        content=content,
                        resource_type=resource_type,
                        tags=','.join(tags)
                    )
        
        try:
            resource = Resource(
                title=title,
                content=content,
                resource_type=resource_type,
                user_id=current_user.id,
                tags=tags,
                file_path=file_path
            )
            resource.save()
            
            flash('Resource created successfully!', 'success')
            return redirect(url_for('resources_list'))
        except Exception as e:
            logger.error(f"Error creating resource: {str(e)}")
            flash(f'Error creating resource: {str(e)}', 'danger')
            return render_template(
                'resources/create.html',
                title=title,
                content=content,
                resource_type=resource_type,
                tags=','.join(tags)
            )
    
    return render_template('resources/create.html')

@app.route('/resources/<resource_id>')
@login_required
def resource_detail(resource_id):
    resource = Resource.get_by_id(resource_id)
    
    if not resource:
        flash('Resource not found.', 'danger')
        return redirect(url_for('resources_list'))
    
    # Get user info for the resource
    resource_user = User.get_by_id(resource.user_id)
    
    return render_template(
        'resources/detail.html',
        resource=resource,
        resource_user=resource_user
    )

@app.route('/resources/<resource_id>/bookmark', methods=['POST'])
@login_required
def toggle_resource_bookmark(resource_id):
    resource = Resource.get_by_id(resource_id)
    
    if not resource:
        return jsonify({'success': False, 'message': 'Resource not found.'})
    
    try:
        is_bookmarked = resource.toggle_bookmark()
        return jsonify({
            'success': True,
            'is_bookmarked': is_bookmarked
        })
    except Exception as e:
        logger.error(f"Error toggling bookmark: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/uploads/<path:filename>')
@login_required
def download_file(filename):
    uploads_dir = os.path.join(app.static_folder, 'uploads')
    return send_from_directory(uploads_dir, filename, as_attachment=True)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', query='', queries=[], resources=[])
    
    # Search for queries (title and content)
    search_queries = db.queries.find({
        '$or': [
            {'title': {'$regex': query, '$options': 'i'}},
            {'content': {'$regex': query, '$options': 'i'}}
        ]
    }).sort('created_at', -1).limit(10)
    
    queries = []
    for q_data in search_queries:
        q = Query(
            title=q_data['title'],
            content=q_data['content'],
            priority=q_data['priority'],
            user_id=q_data['user_id'],
            status=q_data['status'],
            id=q_data['_id'],
            created_at=q_data.get('created_at'),
            updated_at=q_data.get('updated_at'),
            responses=q_data.get('responses', [])
        )
        queries.append(q)
    
    # Search for resources
    resources = Resource.search(query)
    
    return render_template(
        'search.html',
        query=query,
        queries=queries,
        resources=resources
    )

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('errors/500.html'), 500

# Run the application
if __name__ == '__main__':
    app.run(debug=True)