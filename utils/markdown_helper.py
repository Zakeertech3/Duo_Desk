import re
import markdown
from markupsafe import Markup

def md_to_html(text):
    """Convert markdown text to HTML."""
    if not text:
        return ""
    
    # Initialize Markdown converter with extensions
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists'
    ])
    
    # Convert markdown to HTML
    html = md.convert(text)
    
    # Return as safe markup
    return Markup(html)

def excerpt(text, max_length=100):
    """Get an excerpt from text, stripping markdown."""
    if not text:
        return ""
    
    # Strip markdown syntax
    text = re.sub(r'#+ ', '', text)  # Remove headers
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Remove images
    text = re.sub(r'\[.*?\]\(.*?\)', r'\1', text)  # Replace links with link text
    text = re.sub(r'[*_~]{1,2}(.*?)[*_~]{1,2}', r'\1', text)  # Remove formatting
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # Remove code blocks
    text = re.sub(r'`.*?`', '', text)  # Remove inline code
    
    # Truncate to max length
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    
    return text