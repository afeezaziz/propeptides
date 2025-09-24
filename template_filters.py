"""
Custom template filters for the Flask application
"""

import markdown
from markupsafe import Markup
import bleach
from flask import Blueprint

# Create a blueprint for template filters (though we'll register them directly)
filters_bp = Blueprint('filters', __name__)

def markdown_filter(text):
    """Convert markdown text to sanitized HTML"""
    if text is None:
        return ""

    # Configure markdown with extensions
    md = markdown.Markdown(extensions=[
        'extra',          # Tables, fenced code blocks, etc.
        'codehilite',     # Syntax highlighting
        'toc',            # Table of contents
        'nl2br',          # New line to break
        'sane_lists',     # Better list handling
        'tables',         # Table support
        'fenced_code',    # Fenced code blocks
    ])
    html = md.convert(text)

    # Allow a safe subset of tags/attributes
    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union({
        'p', 'pre', 'code', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'table', 'thead', 'tbody', 'tr', 'th', 'td', 'blockquote', 'hr'
    })
    allowed_attributes = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'rel'],
        'img': ['src', 'alt', 'title'],
        'span': ['class'],
        'code': ['class'],
        'pre': ['class'],
    }
    cleaned = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=['http', 'https', 'mailto'],
        strip=True
    )
    # Convert bare links to anchors
    cleaned = bleach.linkify(cleaned)
    return Markup(cleaned)

def excerpt_filter(text, length=150):
    """Create an excerpt from text"""
    if text is None:
        return ""

    # Remove markdown formatting
    import re
    text = re.sub(r'[#*`\[\]()]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) <= length:
        return text

    return text[:length].rstrip() + '...'

def reading_time_filter(text):
    """Calculate estimated reading time"""
    if text is None:
        return "1 min read"

    # Remove markdown and count words
    import re
    text = re.sub(r'[#*`\[\]()]', '', text)
    words = len(text.split())

    # Average reading speed: 200 words per minute
    minutes = max(1, round(words / 200))

    return f"{minutes} min read"

def truncate_filter(text, length=50, end='...'):
    """Truncate text to specified length"""
    if text is None:
        return ""

    if len(text) <= length:
        return text

    return text[:length].rstrip() + end