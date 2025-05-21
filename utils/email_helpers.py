import logging
from flask import current_app, render_template, url_for
from flask_mail import Message
from models.user import User

logger = logging.getLogger(__name__)

def send_email(mail, subject, recipient_email, template_name, **kwargs):
    """Send an email using the provided Mail instance."""
    if not mail or not recipient_email:
        logger.warning("Cannot send email: missing mail instance or recipient")
        return False
    
    # Log the actual email being used
    logger.info(f"Attempting to send email '{subject}' to: {recipient_email}")
    
    # Check if email notifications are enabled
    if not current_app.config.get('MAIL_NOTIFICATIONS_ENABLED', False):
        logger.info(f"Email notifications disabled. Would have sent '{subject}' to {recipient_email}")
        return False
    
    # Check if SMTP credentials are configured
    if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
        logger.warning("Cannot send email: SMTP credentials not configured")
        return False
    
    try:
        msg = Message(
            subject,
            recipients=[recipient_email],
            html=render_template(f"emails/{template_name}.html", **kwargs),
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        logger.info(f"Email sent: '{subject}' to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email to {recipient_email}: {str(e)}")
        return False

def notify_high_priority_query(mail, query, creator_id):
    """Send notification for high priority query."""
    if query.priority != 'high':
        return False
    
    creator = User.get_by_id(creator_id)
    if not creator:
        logger.warning(f"Cannot send high priority notification: creator {creator_id} not found")
        return False
    
    # DIRECTLY USE THE EMAIL ADDRESS FOR TESTING
    recipient_email = 'tanmaiyee.vadloori@gmail.com'
    
    # Get recipient user object
    recipient = None
    for user in User.get_all_users():
        if user.email == recipient_email:
            recipient = user
            break
    
    if not recipient:
        logger.warning(f"Cannot send high priority notification: recipient with email {recipient_email} not found")
        return False
    
    # Generate absolute URL for the query
    query_url = url_for('query_detail', query_id=query.id, _external=True)
    
    return send_email(
        mail,
        f"High Priority Query: {query.title}",
        recipient_email,
        "high_priority_email",
        query=query,
        recipient=recipient,
        creator=creator,
        url=query_url
    )

def notify_new_response(mail, query, response, responder_id):
    """Send notification for new response."""
    responder = User.get_by_id(responder_id)
    if not responder:
        logger.warning(f"Cannot send response notification: responder {responder_id} not found")
        return False
    
    query_creator = User.get_by_id(query.user_id)
    if not query_creator:
        logger.warning(f"Cannot send response notification: query creator {query.user_id} not found")
        return False
    
    # If the responder is the same as the query creator, don't send notification
    if responder_id == query.user_id:
        logger.info("Skipping response notification: responder is the query creator")
        return False
    
    # DIRECTLY USE THE EMAIL ADDRESS BASED ON WHO CREATED THE QUERY
    if query_creator.email == 'zakeer1410@gmail.com':
        recipient_email = 'zakeer1410@gmail.com'
    else:
        recipient_email = 'tanmaiyee.vadloori@gmail.com'
    
    # Generate absolute URL for the query
    query_url = url_for('query_detail', query_id=query.id, _external=True)
    
    return send_email(
        mail,
        f"New Response to Query: {query.title}",
        recipient_email,
        "new_response",
        query=query,
        response=response,
        recipient=query_creator,
        responder=responder,
        url=query_url
    )

def notify_status_update(mail, query, updater_id, previous_status):
    """Send notification for status update."""
    if query.status == previous_status:
        return False
    
    updater = User.get_by_id(updater_id)
    if not updater:
        logger.warning(f"Cannot send status update notification: updater {updater_id} not found")
        return False
    
    query_creator = User.get_by_id(query.user_id)
    if not query_creator:
        logger.warning(f"Cannot send status update notification: query creator {query.user_id} not found")
        return False
    
    # If the updater is the same as the query creator, and it's not a "resolved" update,
    # don't send notification (people don't need to be notified of their own status changes)
    if updater_id == query.user_id and query.status != 'resolved':
        logger.info("Skipping status notification: updater is the query creator")
        return False
    
    # DIRECTLY USE THE EMAIL ADDRESS OF THE OTHER USER
    recipient_email = 'tanmaiyee.vadloori@gmail.com' if updater.email == 'zakeer1410@gmail.com' else 'zakeer1410@gmail.com'
    
    # Get recipient user object
    recipient = None
    for user in User.get_all_users():
        if user.email == recipient_email:
            recipient = user
            break
    
    if not recipient:
        logger.warning(f"Cannot send status update notification: recipient with email {recipient_email} not found")
        return False
    
    # Generate absolute URL for the query
    query_url = url_for('query_detail', query_id=query.id, _external=True)
    
    return send_email(
        mail,
        f"Query Status Updated: {query.title}",
        recipient_email,
        "status_updated",
        query=query,
        recipient=recipient,
        updater=updater,
        previous_status=previous_status,
        url=query_url
    )