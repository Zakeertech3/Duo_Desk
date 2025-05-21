import os
import uuid
from datetime import datetime
from flask import current_app
from markupsafe import Markup  # Changed from flask import Markup
from werkzeug.utils import secure_filename
from flask_mail import Message

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file):
    """Save uploaded file and return the file path."""
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Save the file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Return the relative path for storage in the database
        return os.path.join('uploads', unique_filename)
    
    return None

def format_datetime(dt):
    """Format datetime for display."""
    if not dt:
        return ""
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days == 0:
        # Less than 24 hours
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return dt.strftime("%b %d, %Y")

def nl2br(value):
    """Convert newlines to HTML line breaks."""
    if not value:
        return ""
    
    # Convert newlines to <br> tags
    result = value.replace('\n', '<br>')
    return Markup(result)

def send_notification_email(mail, subject, recipient, template, **kwargs):
    """Send notification email."""
    if not mail or not recipient:
        return False
    
    try:
        msg = Message(
            subject,
            recipients=[recipient]
        )
        msg.html = template.render(**kwargs)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def get_priority_class(priority):
    """Get CSS class for priority level."""
    priority_classes = {
        'low': 'priority-low',
        'medium': 'priority-medium',
        'high': 'priority-high'
    }
    return priority_classes.get(priority, '')

def get_status_class(status):
    """Get CSS class for status."""
    status_classes = {
        'pending': 'status-pending',
        'in_progress': 'status-progress',
        'resolved': 'status-resolved'
    }
    return status_classes.get(status, '')