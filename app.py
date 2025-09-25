from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session
from flask_login import login_required, current_user, login_user, logout_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from auth import google_auth, login_manager, create_or_update_user
from models import (
    db, Post, Product, Category, CartItem, Order, OrderItem, Payment, User,
    PeptideCycle, DosageLog, ProgressEntry,
    CommunityPost, CommunityComment, CommunityVote, CommunityTag,
    FavoriteProduct, StockAlert, NewsletterSubscriber,
    SearchDocument
)
from dotenv import load_dotenv
import re
import os
import io
import csv
import requests
import secrets
import uuid
import pymysql
from datetime import datetime
from sqlalchemy import or_, func, text, event

# Optional AI provider (OpenAI)
try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask app
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
# Allow overriding cookie security for local dev
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour

# Initialize SQLAlchemy
from models import db
db.init_app(app)

# Enable CSRF protection
csrf = CSRFProtect(app)

# Make csrf_token() available in all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Register template filters
from template_filters import markdown_filter, excerpt_filter, reading_time_filter, truncate_filter
app.jinja_env.filters['markdown'] = markdown_filter
app.jinja_env.filters['excerpt'] = excerpt_filter
app.jinja_env.filters['reading_time'] = reading_time_filter
app.jinja_env.filters['truncate'] = truncate_filter

login_manager.init_app(app)

# Global template context (inject cart count into all templates)
@app.context_processor
def inject_cart_count():
    try:
        if current_user.is_authenticated:
            # Sum of quantities in the cart for the current user
            count = db.session.query(func.coalesce(db.func.sum(CartItem.quantity), 0)).filter(
                CartItem.user_id == current_user.id
            ).scalar() or 0
            return {"cart_count": int(count)}
    except Exception:
        # Be resilient if DB not reachable
        pass

    return {"cart_count": 0}

# Marketing config into templates
@app.context_processor
def inject_marketing_config():
    return {
        'GA_ID': os.getenv('GA_MEASUREMENT_ID'),
        'META_PIXEL_ID': os.getenv('META_PIXEL_ID')
    }

# Favorites context for templates
@app.context_processor
def inject_favorites():
    try:
        if current_user.is_authenticated:
            fav_ids = [fp.product_id for fp in FavoriteProduct.query.filter_by(user_id=current_user.id).all()]
            return {"favorite_product_ids": set(fav_ids)}
    except Exception:
        pass
    return {"favorite_product_ids": set()}

# Capture UTM parameters and referrer on first session hit
@app.before_request
def capture_utm_referrer():
    try:
        if 'utm_captured' not in session:
            utm = {}
            for key in ('utm_source', 'utm_medium', 'utm_campaign'):
                val = request.args.get(key)
                if val:
                    utm[key] = val
            if utm:
                session['utm'] = utm
            # Capture initial referrer
            ref = request.headers.get('Referer') or request.headers.get('Referrer')
            if ref:
                session['referrer'] = ref
            session['utm_captured'] = True
    except Exception:
        pass


# Helper functions
def generate_slug(title):
    """Generate URL-friendly slug from title"""
    return title.lower().replace(' ', '-').replace('_', '-')

def unique_slug(base: str, model_class, field: str = 'slug'):
    """Ensure slug uniqueness for a given model by appending a counter if needed."""
    base_slug = generate_slug(base)
    slug = base_slug
    counter = 2
    while db.session.query(model_class).filter(getattr(model_class, field) == slug).first() is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

def generate_order_number():
    """Generate unique order number"""
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

# Optionally auto-create tables in dev to avoid migration steps locally
if os.getenv('AUTO_CREATE_TABLES', 'false').lower() == 'true':
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass

# Initialize pgvector extension if using Postgres
def init_pgvector():
    try:
        with app.app_context():
            if db.engine.dialect.name in ('postgresql', 'postgres'):
                with db.engine.connect() as conn:
                    conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
                    conn.commit()
    except Exception:
        pass

init_pgvector()

@app.route('/')
def index():
    # Fetch latest published posts for homepage blog section
    latest_posts = Post.query.filter_by(status='published').order_by(Post.created_at.desc()).limit(3).all()
    return render_template('index.html', posts=latest_posts)

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Preserve next path if present so we can return after Google OAuth
    next_url = request.args.get('next')
    auth_url = google_auth.get_auth_url(state=next_url) if next_url else google_auth.get_auth_url()
    return render_template('login.html', auth_url=auth_url)

@app.route('/authorize')
def authorize():
    if 'code' not in request.args:
        flash('Authorization failed', 'error')
        return redirect(url_for('login'))

    try:
        # Get access token
        token_response = google_auth.get_token(request.args['code'])
        if 'error' in token_response:
            flash('Failed to get access token', 'error')
            return redirect(url_for('login'))

        # Get user info
        user_info = google_auth.get_user_info(token_response['access_token'])

        # Create or update user
        user = create_or_update_user(user_info)
        login_user(user)

        flash('Successfully logged in!', 'success')
        # Redirect back to the original page if provided via state and is a safe relative path
        state_next = request.args.get('state')
        if state_next and isinstance(state_next, str) and state_next.startswith('/'):
            return redirect(state_next)
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Blog Posts Routes
@app.route('/posts')
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(status='published').order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('posts/index.html', posts=posts)

@app.route('/posts/<slug>')
def post_detail(slug):
    post = Post.query.filter_by(slug=slug, status='published').first_or_404()

    # Get related posts based on content similarity and tags
    related_posts = get_related_posts(post, limit=3)

    # Previous and next posts based on publication date
    prev_post = Post.query.filter(
        Post.status == 'published',
        Post.created_at < post.created_at
    ).order_by(Post.created_at.desc()).first()

    next_post = Post.query.filter(
        Post.status == 'published',
        Post.created_at > post.created_at
    ).order_by(Post.created_at.asc()).first()

    # Increment view count (best-effort)
    try:
        post.view_count = (post.view_count or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()

    return render_template(
        'posts/detail.html',
        post=post,
        related_posts=related_posts,
        prev_post=prev_post,
        next_post=next_post
    )

def get_related_posts(current_post, limit=3):
    """Get related posts using pgvector if available, else keyword similarity."""
    # Try vector-based retrieval from SearchDocument when using Postgres + pgvector
    if OpenAI and os.getenv('OPENAI_API_KEY') and db.engine.dialect.name in ('postgresql', 'postgres'):
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            embed_model = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
            seed = f"{current_post.title}\n{current_post.excerpt or ''}\n{current_post.content or ''}"
            emb = client.embeddings.create(model=embed_model, input=seed).data[0].embedding
            docs = (SearchDocument.query
                    .filter(SearchDocument.kind == 'post', SearchDocument.ref_id != current_post.id)
                    .order_by(SearchDocument.embedding.cosine_distance(emb))  # type: ignore
                    .limit(limit * 3)
                    .all())
            related = []
            for d in docs:
                p = Post.query.filter_by(id=d.ref_id, status='published').first()
                if p and p.id != current_post.id and p not in related:
                    related.append(p)
                if len(related) >= limit:
                    break
            if related:
                return related
        except Exception:
            pass

    # Fallback: keyword similarity on title/excerpt/content
    current_keywords = extract_keywords((current_post.title or '') + ' ' + (current_post.excerpt or ''))
    all_posts = Post.query.filter(Post.status == 'published', Post.id != current_post.id).all()
    scored_posts = []
    for post in all_posts:
        post_keywords = extract_keywords((post.title or '') + ' ' + (post.excerpt or ''))
        score = calculate_similarity(current_keywords, post_keywords)
        if has_similar_theme(current_post.content, post.content):
            score += 2
        if score > 0:
            scored_posts.append((post, score))
    scored_posts.sort(key=lambda x: x[1], reverse=True)
    return [post for post, score in scored_posts[:limit]]

def get_relevant_content(query_text: str, top_n: int = 3):
    """Return top_n relevant products and posts. Prefer vector search (pgvector) if available, else fallback to keyword similarity."""
    use_vector = OpenAI and os.getenv('OPENAI_API_KEY') and db.engine.dialect.name in ('postgresql', 'postgres')

    if use_vector:
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            embed_model = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
            emb = client.embeddings.create(model=embed_model, input=query_text).data[0].embedding

            # Order by cosine distance ascending (most similar first)
            docs = SearchDocument.query.order_by(SearchDocument.embedding.cosine_distance(emb)).limit(top_n * 4).all()  # type: ignore

            prods, posts = [], []
            for d in docs:
                if d.kind == 'product' and len(prods) < top_n:
                    p = Product.query.filter_by(id=d.ref_id, status='active').first()
                    if p:
                        prods.append(p)
                elif d.kind == 'post' and len(posts) < top_n:
                    post = Post.query.filter_by(id=d.ref_id, status='published').first()
                    if post:
                        posts.append(post)
                if len(prods) >= top_n and len(posts) >= top_n:
                    break
            return prods, posts
        except Exception:
            pass

    # Fallback: keyword similarity
    keywords = extract_keywords(query_text)
    prod_scores = []
    for p in Product.query.filter_by(status='active').all():
        txt = f"{p.name} {p.short_description or ''} {p.description or ''}"
        score = calculate_similarity(keywords, extract_keywords(txt))
        if score > 0:
            prod_scores.append((p, score))
    prod_scores.sort(key=lambda x: x[1], reverse=True)
    top_products = [p for p, _ in prod_scores[:top_n]]

    post_scores = []
    for post in Post.query.filter_by(status='published').all():
        txt = f"{post.title} {post.excerpt or ''} {post.content or ''}"
        score = calculate_similarity(keywords, extract_keywords(txt))
        if score > 0:
            post_scores.append((post, score))
    post_scores.sort(key=lambda x: x[1], reverse=True)
    top_posts = [p for p, _ in post_scores[:top_n]]

    return top_products, top_posts

def upsert_search_documents(limit: int | None = None):
    """Ensure SearchDocument rows exist with embeddings for active products, published posts, and community posts."""
    if not (OpenAI and os.getenv('OPENAI_API_KEY') and db.engine.dialect.name in ('postgresql', 'postgres')):
        return 0
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    embed_model = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')

    def ensure(kind: str, ref_id: int, title: str, slug: str, text_body: str):
        doc = SearchDocument.query.filter_by(kind=kind, ref_id=ref_id).first()
        if not doc:
            doc = SearchDocument(kind=kind, ref_id=ref_id, title=title, slug=slug)
            db.session.add(doc)
        else:
            doc.title = title
            doc.slug = slug
        emb = client.embeddings.create(model=embed_model, input=text_body).data[0].embedding
        # Assign embedding vector
        try:
            doc.embedding = emb  # type: ignore
        except Exception:
            pass
        return doc

    count = 0
    products = Product.query.filter_by(status='active').all()
    posts = Post.query.filter_by(status='published').all()
    cposts = CommunityPost.query.filter_by(status='published').all()
    if limit:
        products = products[:limit]
        posts = posts[:limit]
        cposts = cposts[:limit]

    for p in products:
        body = f"{p.name}\n{p.short_description or ''}\n{p.description or ''}"
        ensure('product', p.id, p.name, p.slug, body)
        count += 1
    for post in posts:
        body = f"{post.title}\n{post.excerpt or ''}\n{post.content or ''}"
        ensure('post', post.id, post.title, post.slug, body)
        count += 1
    for cp in cposts:
        body = f"{cp.title}\n{cp.content or ''}"
        ensure('community', cp.id, cp.title, cp.slug, body)
        count += 1
    db.session.commit()
    return count

def upsert_single_document(kind: str, ref_id: int):
    """Upsert a single SearchDocument row + embedding for a given kind/id."""
    if not (OpenAI and os.getenv('OPENAI_API_KEY') and db.engine.dialect.name in ('postgresql', 'postgres')):
        return False
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    embed_model = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')

    if kind == 'product':
        p = Product.query.get(ref_id)
        if not p or p.status != 'active':
            return False
        title, slug = p.name, p.slug
        body = f"{p.name}\n{p.short_description or ''}\n{p.description or ''}"
    elif kind == 'post':
        post = Post.query.get(ref_id)
        if not post or post.status != 'published':
            return False
        title, slug = post.title, post.slug
        body = f"{post.title}\n{post.excerpt or ''}\n{post.content or ''}"
    elif kind == 'community':
        cp = CommunityPost.query.get(ref_id)
        if not cp or cp.status != 'published':
            return False
        title, slug = cp.title, cp.slug
        body = f"{cp.title}\n{cp.content or ''}"
    else:
        return False

    doc = SearchDocument.query.filter_by(kind=kind, ref_id=ref_id).first()
    if not doc:
        doc = SearchDocument(kind=kind, ref_id=ref_id, title=title, slug=slug)
        db.session.add(doc)
    else:
        doc.title = title
        doc.slug = slug
    emb = client.embeddings.create(model=embed_model, input=body).data[0].embedding
    try:
        doc.embedding = emb  # type: ignore
    except Exception:
        pass
    db.session.commit()
    return True

# ---------------------------------
# Newsletter + RSS + Sitemap Routes
# ---------------------------------

@app.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = (request.form.get('email') or '').strip().lower()
    name = (request.form.get('name') or '').strip()
    if not email or '@' not in email:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Please enter a valid email.'}), 400
        flash('Please enter a valid email.', 'error')
        return redirect(request.referrer or url_for('posts'))

    sub = NewsletterSubscriber.query.filter_by(email=email).first()
    if not sub:
        sub = NewsletterSubscriber(email=email)
        db.session.add(sub)
    # Update optional fields
    if name:
        sub.name = name
    utm = session.get('utm') or {}
    sub.utm_source = utm.get('utm_source')
    sub.utm_medium = utm.get('utm_medium')
    sub.utm_campaign = utm.get('utm_campaign')
    sub.referrer = session.get('referrer')
    sub.user_agent = request.headers.get('User-Agent')
    sub.ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    # Reactivate and set unsubscribe token if needed
    sub.active = True
    sub.unsubscribed_at = None
    if not getattr(sub, 'unsubscribe_token', None):
        sub.unsubscribe_token = secrets.token_hex(16)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Subscription failed. Please try again later.'}), 500
        flash('Subscription failed. Please try again later.', 'error')
        return redirect(request.referrer or url_for('posts'))

    # Optional: add to Mailgun list if configured
    try:
        mg_key = os.getenv('MAILGUN_API_KEY')
        mg_list = os.getenv('MAILGUN_LIST_ADDRESS')
        if mg_key and mg_list:
            requests.post(
                f"https://api.mailgun.net/v3/lists/{mg_list}/members",
                auth=("api", mg_key),
                data={
                    'address': email,
                    'name': name,
                    'subscribed': 'yes',
                    'upsert': 'yes'
                },
                timeout=8
            )
    except Exception:
        # Ignore provider errors silently in app flow
        pass

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    flash('Subscribed! Please check your inbox for updates.', 'success')
    return redirect(request.referrer or url_for('posts'))

@app.route('/newsletter/unsubscribe/<token>')
def newsletter_unsubscribe(token):
    sub = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    if not sub:
        flash('Invalid unsubscribe link.', 'error')
        return redirect(url_for('posts'))
    try:
        sub.active = False
        sub.unsubscribed_at = datetime.utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Failed to update subscription. Please try again later.', 'error')
        return redirect(url_for('posts'))
    return render_template('newsletter/unsubscribed.html', email=sub.email)

@app.route('/rss.xml')
def rss_feed():
    from flask import Response
    site_url = os.getenv('SITE_URL', request.url_root.rstrip('/'))
    items = Post.query.filter_by(status='published').order_by(Post.created_at.desc()).limit(20).all()
    rss_items = []
    for p in items:
        link = f"{site_url}{url_for('post_detail', slug=p.slug).lstrip('/')}"
        desc = (p.excerpt or p.meta_description or '')
        rss_items.append(f"""
        <item>
          <title>{(p.title or '').replace('&', '&amp;')}</title>
          <link>{link}</link>
          <guid isPermaLink="true">{link}</guid>
          <pubDate>{p.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
          <description><![CDATA[{desc}]]></description>
        </item>
        """)
    rss = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Propeptides Blog</title>
    <link>{site_url}/posts</link>
    <description>Latest articles from Propeptides</description>
    {''.join(rss_items)}
  </channel>
</rss>"""
    return Response(rss, mimetype='application/rss+xml')

@app.route('/sitemap.xml')
def sitemap_xml():
    from flask import Response
    site_url = os.getenv('SITE_URL', request.url_root.rstrip('/'))
    urls = []
    # Static important URLs
    for endpoint in ['index', 'peptides', 'posts', 'calculator', 'tracker', 'search', 'assistant']:
        try:
            urls.append({'loc': f"{site_url}{url_for(endpoint).lstrip('/')}", 'priority': '0.8'})
        except Exception:
            pass
    # Blog posts
    for p in Post.query.filter_by(status='published').order_by(Post.created_at.desc()).all():
        urls.append({'loc': f"{site_url}{url_for('post_detail', slug=p.slug).lstrip('/')}", 'priority': '0.7'})
    # Products
    for pr in Product.query.filter_by(status='active').order_by(Product.created_at.desc()).all():
        urls.append({'loc': f"{site_url}{url_for('peptide_detail', slug=pr.slug).lstrip('/')}", 'priority': '0.6'})

    xml_items = []
    for u in urls:
        xml_items.append(f"<url><loc>{u['loc']}</loc><priority>{u['priority']}</priority></url>")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(xml_items)}
</urlset>"""
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots_txt():
    from flask import Response
    site_url = os.getenv('SITE_URL', request.url_root.rstrip('/'))
    lines = [
        'User-agent: *',
        'Disallow:',
        f'Sitemap: {site_url}/sitemap.xml'
    ]
    return Response("\n".join(lines), mimetype='text/plain')

# Auto-embed on changes to Product/Post using session events
if os.getenv('AUTO_EMBED', 'true').lower() == 'true':
    @event.listens_for(db.session, 'after_flush')
    def _collect_changed_objects(session, flush_context):
        ids = session.info.setdefault('auto_embed_ids', {
            'product': set(), 'post': set(), 'community': set(),
            'delete_product': set(), 'delete_post': set(), 'delete_community': set()
        })
        for obj in session.new.union(session.dirty):
            try:
                if isinstance(obj, Product) and obj.id:
                    ids['product'].add(obj.id)
                elif isinstance(obj, Post) and obj.id:
                    ids['post'].add(obj.id)
                elif isinstance(obj, CommunityPost) and obj.id:
                    ids['community'].add(obj.id)
            except Exception:
                continue
        for obj in session.deleted:
            try:
                if isinstance(obj, Product) and obj.id:
                    ids['delete_product'].add(obj.id)
                elif isinstance(obj, Post) and obj.id:
                    ids['delete_post'].add(obj.id)
                elif isinstance(obj, CommunityPost) and obj.id:
                    ids['delete_community'].add(obj.id)
            except Exception:
                continue

    @event.listens_for(db.session, 'after_commit')
    def _run_auto_embed(session):
        ids = session.info.pop('auto_embed_ids', None)
        if not ids:
            return
        try:
            for pid in ids.get('product', []):
                upsert_single_document('product', pid)
            for tid in ids.get('post', []):
                upsert_single_document('post', tid)
            for cid in ids.get('community', []):
                upsert_single_document('community', cid)
            # Deletes
            delp = list(ids.get('delete_product', []) or [])
            if delp:
                SearchDocument.query.filter(
                    SearchDocument.kind == 'product', SearchDocument.ref_id.in_(delp)
                ).delete(synchronize_session=False)
            delt = list(ids.get('delete_post', []) or [])
            if delt:
                SearchDocument.query.filter(
                    SearchDocument.kind == 'post', SearchDocument.ref_id.in_(delt)
                ).delete(synchronize_session=False)
            delc = list(ids.get('delete_community', []) or [])
            if delc:
                SearchDocument.query.filter(
                    SearchDocument.kind == 'community', SearchDocument.ref_id.in_(delc)
                ).delete(synchronize_session=False)
            if delp or delt or delc:
                db.session.commit()
        except Exception:
            pass

# ----------------------
# Site-wide Search
# ----------------------

def _vector_search_documents(query_text: str, limit: int = 30):
    """Return SearchDocument rows ordered by vector similarity if available, else empty list."""
    if not (OpenAI and os.getenv('OPENAI_API_KEY') and db.engine.dialect.name in ('postgresql', 'postgres')):
        return []
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        embed_model = os.getenv('OPENAI_EMBED_MODEL', 'text-embedding-3-small')
        emb = client.embeddings.create(model=embed_model, input=query_text).data[0].embedding
        return SearchDocument.query.order_by(
            SearchDocument.embedding.cosine_distance(emb)  # type: ignore
        ).limit(limit).all()
    except Exception:
        return []

@app.route('/search')
def search():
    q = request.args.get('q', '', type=str).strip()
    type_filter = request.args.get('type', 'all')  # all | product | post | community
    category_slug = request.args.get('category', None, type=str)
    min_price = request.args.get('min_price', None, type=float)
    max_price = request.args.get('max_price', None, type=float)
    sort = request.args.get('sort', 'relevance')  # relevance | price_low | price_high | newest | name_asc | name_desc
    in_stock = request.args.get('in_stock', default=None)
    on_sale = request.args.get('on_sale', default=None)

    categories = Category.query.order_by(Category.name.asc()).all()
    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()

    results = []
    counts = {'product': 0, 'post': 0, 'community': 0}

    def product_passes_filters(p: Product) -> bool:
        if selected_category and p.category_id != selected_category.id:
            return False
        price_val = float(p.sale_price if p.sale_price is not None else p.price)
        if min_price is not None and price_val < float(min_price):
            return False
        if max_price is not None and price_val > float(max_price):
            return False
        if in_stock in ('1', 'true', 'True') and not p.is_in_stock():
            return False
        if on_sale in ('1', 'true', 'True') and p.sale_price is None:
            return False
        return True

    if q:
        docs = _vector_search_documents(q, limit=50)
        used_vector = bool(docs)
        if not used_vector:
            # Fallback keyword search
            kw = extract_keywords(q)
            # rank products
            for p in Product.query.filter_by(status='active').all():
                txt = f"{p.name} {p.short_description or ''} {p.description or ''} {p.sku} {(p.category.name if p.category else '')}"
                score = calculate_similarity(kw, extract_keywords(txt))
                if score > 0 and (type_filter in ('all', 'product')) and product_passes_filters(p):
                    results.append({
                        'kind': 'product',
                        'title': p.name,
                        'url': url_for('peptide_detail', slug=p.slug),
                        'score': score,
                        'snippet': p.short_description or '',
                        'price': float(p.sale_price if p.sale_price is not None else p.price),
                        'sale_price': float(p.sale_price) if p.sale_price is not None else None,
                        'category': p.category.slug if p.category else None,
                        'created_at': p.created_at,
                        'id': p.id,
                        'in_stock': p.is_in_stock(),
                    })
                    counts['product'] += 1
            # rank posts
            for post in Post.query.filter_by(status='published').all():
                if type_filter not in ('all', 'post'):
                    continue
                txt = f"{post.title} {post.excerpt or ''} {post.content or ''}"
                score = calculate_similarity(kw, extract_keywords(txt))
                if score > 0:
                    results.append({
                        'kind': 'post',
                        'title': post.title,
                        'url': url_for('post_detail', slug=post.slug),
                        'score': score,
                        'snippet': post.excerpt or '',
                        'created_at': post.created_at,
                        'id': post.id,
                    })
                    counts['post'] += 1
            # rank community posts
            for cpost in CommunityPost.query.filter_by(status='published').all():
                if type_filter not in ('all', 'community'):
                    continue
                txt = f"{cpost.title} {cpost.content or ''}"
                score = calculate_similarity(kw, extract_keywords(txt))
                if score > 0:
                    results.append({
                        'kind': 'community',
                        'title': cpost.title,
                        'url': url_for('community_detail', slug=cpost.slug),
                        'score': score,
                        'snippet': (cpost.content or '')[:200],
                        'created_at': cpost.created_at,
                        'id': cpost.id,
                    })
                    counts['community'] += 1
            # Default relevance order: score desc
            results.sort(key=lambda r: r.get('score') or 0, reverse=True)
        else:
            # Build results from vector docs, preserving order initially
            for d in docs:
                if d.kind == 'product' and type_filter in ('all', 'product'):
                    p = Product.query.filter_by(id=d.ref_id, status='active').first()
                    if p and product_passes_filters(p):
                        results.append({
                            'kind': 'product',
                            'title': p.name,
                            'url': url_for('peptide_detail', slug=p.slug),
                            'score': None,
                            'snippet': p.short_description or '',
                            'price': float(p.sale_price if p.sale_price is not None else p.price),
                            'sale_price': float(p.sale_price) if p.sale_price is not None else None,
                            'category': p.category.slug if p.category else None,
                            'created_at': p.created_at,
                            'id': p.id,
                            'in_stock': p.is_in_stock(),
                        })
                        counts['product'] += 1
                elif d.kind == 'post' and type_filter in ('all', 'post'):
                    post = Post.query.filter_by(id=d.ref_id, status='published').first()
                    if post:
                        results.append({
                            'kind': 'post',
                            'title': post.title,
                            'url': url_for('post_detail', slug=post.slug),
                            'score': None,
                            'snippet': post.excerpt or '',
                            'created_at': post.created_at,
                            'id': post.id,
                        })
                        counts['post'] += 1
                elif d.kind == 'community' and type_filter in ('all', 'community'):
                    cp = CommunityPost.query.filter_by(id=d.ref_id, status='published').first()
                    if cp:
                        results.append({
                            'kind': 'community',
                            'title': cp.title,
                            'url': url_for('community_detail', slug=cp.slug),
                            'score': None,
                            'snippet': (cp.content or '')[:200],
                            'created_at': cp.created_at,
                            'id': cp.id,
                        })
                        counts['community'] += 1

        # Apply sorting if not relevance (which is default order for vector, and score order for keyword)
        if sort == 'price_low':
            results.sort(key=lambda r: (r.get('price') is None, r.get('price', 0)))
        elif sort == 'price_high':
            results.sort(key=lambda r: (r.get('price') is None, -(r.get('price') or 0)))
        elif sort == 'newest':
            results.sort(key=lambda r: r.get('created_at') or datetime.min, reverse=True)
        elif sort == 'name_asc':
            results.sort(key=lambda r: (r.get('title') or '').lower())
        elif sort == 'name_desc':
            results.sort(key=lambda r: (r.get('title') or '').lower(), reverse=True)

    return render_template(
        'search/index.html',
        q=q,
        results=results,
        counts=counts,
        categories=categories,
        type_filter=type_filter,
        selected_category=selected_category.slug if selected_category else None,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        in_stock=(in_stock in ('1', 'true', 'True')),
        on_sale=(on_sale in ('1', 'true', 'True')),
    )

# ----------------------
# Admin
# ----------------------

@app.route('/admin')
@login_required
def admin_index():
    if getattr(current_user, 'role', '') != 'admin':
        return render_template('errors/403.html'), 403
    stats = {
        'products': Product.query.count(),
        'posts': Post.query.count(),
        'search_documents': SearchDocument.query.count(),
        'subscribers': NewsletterSubscriber.query.count(),
    }
    return render_template('admin/index.html', stats=stats)

@app.route('/admin/clear_index', methods=['POST'])
@login_required
def admin_clear_index():
    if getattr(current_user, 'role', '') != 'admin':
        return render_template('errors/403.html'), 403
    try:
        SearchDocument.query.delete()
        db.session.commit()
        flash('Cleared search index.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to clear index: {str(e)}', 'error')
    return redirect(url_for('admin_index'))

@app.route('/admin/subscribers/export')
@login_required
def admin_export_subscribers():
    if getattr(current_user, 'role', '') != 'admin':
        return render_template('errors/403.html'), 403
    # Build CSV in-memory
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['email', 'name', 'utm_source', 'utm_medium', 'utm_campaign', 'referrer', 'user_agent', 'ip_address', 'created_at'])
    for s in NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all():
        writer.writerow([
            s.email or '', s.name or '', s.utm_source or '', s.utm_medium or '', s.utm_campaign or '',
            s.referrer or '', s.user_agent or '', s.ip_address or '',
            s.created_at.isoformat() if s.created_at else ''
        ])
    data = buf.getvalue()
    from flask import Response
    return Response(
        data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename="newsletter_subscribers.csv"'}
    )

def extract_keywords(text):
    """Extract keywords from text"""
    if not text:
        return []

    # Simple keyword extraction - remove common words and get unique terms
    text = text.lower()
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

    # Filter out common words
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
        'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
        'did', 'she', 'use', 'her', 'than', 'when', 'with', 'have', 'this', 'that', 'from', 'they', 'been', 'have'
    }

    keywords = [word for word in words if word not in stop_words]
    return list(set(keywords))  # Remove duplicates

def calculate_similarity(keywords1, keywords2):
    """Calculate similarity score between two keyword lists"""
    if not keywords1 or not keywords2:
        return 0

    intersection = set(keywords1) & set(keywords2)
    union = set(keywords1) | set(keywords2)

    if not union:
        return 0

    return len(intersection) / len(union)

def has_similar_theme(content1, content2):
    """Check if two posts have similar themes"""
    if not content1 or not content2:
        return False

    # Check for common peptide/drug names
    peptide_terms = ['semaglutide', 'retatrutide', 'tirzepatide', 'liraglutide', 'glp-1', 'gip', 'glucagon',
                     'peptide', 'agonist', 'receptor', 'diabetes', 'obesity', 'weight', 'metabolic']

    content1_lower = content1.lower()
    content2_lower = content2.lower()

    common_terms = []
    for term in peptide_terms:
        if term in content1_lower and term in content2_lower:
            common_terms.append(term)

    return len(common_terms) >= 1

# ----------------------
# Community Routes
# ----------------------

@app.route('/community')
def community_index():
    page = request.args.get('page', 1, type=int)
    tag_slug = request.args.get('tag')
    sort = request.args.get('sort', 'new')  # new, top

    query = CommunityPost.query.filter_by(status='published')
    active_tag = None
    if tag_slug:
        active_tag = CommunityTag.query.filter_by(slug=tag_slug).first()
        if active_tag:
            query = query.join(CommunityPost.tags).filter(CommunityTag.slug == tag_slug)

    if sort == 'top':
        query = query.order_by(CommunityPost.score.desc(), CommunityPost.created_at.desc())
    else:
        query = query.order_by(CommunityPost.created_at.desc())

    posts = query.paginate(page=page, per_page=10, error_out=False)
    tags = CommunityTag.query.order_by(CommunityTag.name.asc()).all()

    return render_template('community/index.html', posts=posts, tags=tags, active_tag=active_tag, sort=sort)

@app.route('/community/new', methods=['GET', 'POST'])
@login_required
def community_new():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        tags_raw = request.form.get('tags', '').strip()

        if not title or not content:
            flash('Title and content are required.', 'error')
            return redirect(url_for('community_new'))

        # Moderation
        if OpenAI and os.getenv('OPENAI_API_KEY') and os.getenv('ENABLE_MODERATION', 'true').lower() == 'true':
            try:
                client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                mod_model = os.getenv('OPENAI_MODERATION_MODEL', 'omni-moderation-latest')
                mod = client.moderations.create(model=mod_model, input=f"{title}\n{content}")
                if mod.results and mod.results[0].flagged:
                    flash('Your post appears to violate our content policy. Please revise.', 'error')
                    return redirect(url_for('community_new'))
            except Exception:
                pass

        slug = unique_slug(title, CommunityPost)
        post = CommunityPost(
            user_id=current_user.id,
            title=title,
            slug=slug,
            content=content,
        )

        # Handle tags
        tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []
        for name in tag_names:
            tag_slug = generate_slug(name)
            tag = CommunityTag.query.filter_by(slug=tag_slug).first()
            if not tag:
                tag = CommunityTag(name=name, slug=tag_slug)
                db.session.add(tag)
            post.tags.append(tag)

        db.session.add(post)
        db.session.commit()

        # Upsert into search documents (best-effort)
        try:
            upsert_search_documents(limit=None)
        except Exception:
            pass

        flash('Community post published!', 'success')
        return redirect(url_for('community_detail', slug=post.slug))

    tags = CommunityTag.query.order_by(CommunityTag.name.asc()).all()
    return render_template('community/new.html', tags=tags)

@app.route('/community/<slug>')
def community_detail(slug):
    post = CommunityPost.query.filter_by(slug=slug, status='published').first_or_404()

    # Increment view count
    try:
        post.view_count = (post.view_count or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Compute current score if needed (sum of votes)
    if post.votes:
        post.score = sum(v.value for v in post.votes)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return render_template('community/detail.html', post=post)

@app.route('/community/<slug>/comment', methods=['POST'])
@login_required
def community_comment(slug):
    post = CommunityPost.query.filter_by(slug=slug, status='published').first_or_404()
    content = request.form.get('content', '').strip()
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('community_detail', slug=slug))

    # Moderation
    if OpenAI and os.getenv('OPENAI_API_KEY') and os.getenv('ENABLE_MODERATION', 'true').lower() == 'true':
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            mod_model = os.getenv('OPENAI_MODERATION_MODEL', 'omni-moderation-latest')
            mod = client.moderations.create(model=mod_model, input=content)
            if mod.results and mod.results[0].flagged:
                flash('Your comment appears to violate our content policy. Please revise.', 'error')
                return redirect(url_for('community_detail', slug=slug))
        except Exception:
            pass

    comment = CommunityComment(post_id=post.id, user_id=current_user.id, content=content)
    db.session.add(comment)
    post.comment_count = (post.comment_count or 0) + 1
    db.session.commit()

    flash('Comment added!', 'success')
    return redirect(url_for('community_detail', slug=slug))

@app.route('/community/<slug>/vote', methods=['POST'])
@login_required
def community_vote(slug):
    post = CommunityPost.query.filter_by(slug=slug, status='published').first_or_404()
    action = request.form.get('value')  # 'up' or 'down'
    if action not in {'up', 'down'}:
        return jsonify({'success': False, 'error': 'Invalid vote value'}), 400

    value = 1 if action == 'up' else -1
    vote = CommunityVote.query.filter_by(post_id=post.id, user_id=current_user.id).first()

    if vote and vote.value == value:
        # Toggle off
        db.session.delete(vote)
    elif vote:
        vote.value = value
    else:
        vote = CommunityVote(post_id=post.id, user_id=current_user.id, value=value)
        db.session.add(vote)

    # Recompute score
    db.session.flush()
    new_score = db.session.query(func.coalesce(db.func.sum(CommunityVote.value), 0)).filter(
        CommunityVote.post_id == post.id
    ).scalar() or 0
    post.score = int(new_score)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'score': post.score})
    return redirect(url_for('community_detail', slug=slug))

@app.route('/admin/reindex', methods=['POST'])
@login_required
def admin_reindex():
    if getattr(current_user, 'role', '') != 'admin':
        return render_template('errors/403.html'), 403
    try:
        count = upsert_search_documents()
        flash(f'Reindexed {count} documents for search.', 'success')
    except Exception as e:
        flash(f'Reindex failed: {str(e)}', 'error')
    return redirect(url_for('admin_index'))

# ----------------------
# AI Assistant
# ----------------------

def ai_generate_answer(message: str, products, posts) -> str:
    disclaimer = (
        "Important: I am an AI research assistant for educational purposes only. "
        "I do not provide medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional."
    )

    # Build a simple context block
    ctx_lines = ["Context summary:"]
    if products:
        ctx_lines.append("Relevant products:")
        for p in products:
            price = float(p.sale_price or p.price)
            link = url_for('peptide_detail', slug=p.slug)
            ctx_lines.append(f"- [{p.name}]({link}) (${price:.2f}): {p.short_description or ''}")
    if posts:
        ctx_lines.append("Relevant blog posts:")
        for post in posts:
            link = url_for('post_detail', slug=post.slug)
            ctx_lines.append(f"- [{post.title}]({link}): {post.excerpt or ''}")
    context_text = "\n".join(ctx_lines)

    if OpenAI and os.getenv('OPENAI_API_KEY'):
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            messages = [
                {"role": "system", "content": (
                    "You are a helpful peptide research assistant for an ecommerce site. "
                    "Follow these rules: \n"
                    "- Do NOT provide medical advice. Include a disclaimer.\n"
                    "- Be concise and cite relevant products/posts by name.\n"
                    "- If unsure, ask a clarifying question."
                )},
                {"role": "user", "content": f"{disclaimer}\n\n{context_text}\n\nQuestion: {message}"}
            ]
            resp = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
            content = resp.choices[0].message.content
            return content
        except Exception:
            pass

    # Fallback heuristic answer
    parts = [disclaimer, "\nHere are some resources that might help:"]
    if products:
        parts.append("Products:")
        for p in products:
            parts.append(f"- {p.name} ({url_for('peptide_detail', slug=p.slug)})")
    if posts:
        parts.append("Blog posts:")
        for post in posts:
            parts.append(f"- {post.title} ({url_for('post_detail', slug=post.slug)})")
    parts.append("\nIf you can share more specifics (goal, timeline, constraints), I can refine suggestions.")
    return "\n".join(parts)

@app.route('/assistant', methods=['GET'])
def assistant():
    history = session.get('assistant_history', [])
    return render_template('assistant/index.html', history=history)

@app.route('/assistant/message', methods=['POST'])
def assistant_message():
    user_message = request.form.get('message', '').strip()
    if not user_message:
        flash('Please enter a message.', 'error')
        return redirect(url_for('assistant'))

    # Moderation check
    if OpenAI and os.getenv('OPENAI_API_KEY') and os.getenv('ENABLE_MODERATION', 'true').lower() == 'true':
        try:
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            mod_model = os.getenv('OPENAI_MODERATION_MODEL', 'omni-moderation-latest')
            mod = client.moderations.create(model=mod_model, input=user_message)
            if mod.results and mod.results[0].flagged:
                flash('Your message appears to violate our content policy. Please rephrase.', 'error')
                return redirect(url_for('assistant'))
        except Exception:
            pass

    # Retrieve context
    products, posts = get_relevant_content(user_message, top_n=3)
    answer = ai_generate_answer(user_message, products, posts)

    # Maintain simple session history
    history = session.get('assistant_history', [])
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": answer})
    session['assistant_history'] = history[-20:]  # cap history

    return redirect(url_for('assistant'))

# Products Routes
@app.route('/peptides')
def peptides():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    q = request.args.get('q', type=str, default='')
    sort = request.args.get('sort', type=str, default='new')  # new, price_low, price_high, name_asc, name_desc

    query = Product.query.filter_by(status='active')
    if category_id:
        query = query.filter_by(category_id=category_id)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Product.name.ilike(like), Product.description.ilike(like)))

    # Sorting
    if sort == 'price_low':
        query = query.order_by(func.coalesce(Product.sale_price, Product.price).asc())
    elif sort == 'price_high':
        query = query.order_by(func.coalesce(Product.sale_price, Product.price).desc())
    elif sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Product.name.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.all()

    return render_template(
        'peptides/index.html',
        products=products,
        categories=categories,
        selected_category=category_id,
        q=q,
        sort=sort,
    )

@app.route('/peptides/<slug>')
def peptide_detail(slug):
    product = Product.query.filter_by(slug=slug, status='active').first_or_404()
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.status == 'active'
    ).limit(4).all()
    # Recently viewed products (session-based)
    try:
        rv = session.get('recently_viewed_products', [])
        # Move current to front
        rv = [s for s in rv if s != product.slug]
        rv.insert(0, product.slug)
        session['recently_viewed_products'] = rv[:8]

        # Fetch recently viewed excluding current
        recent_slugs = [s for s in rv if s != product.slug][:8]
        if recent_slugs:
            recently_viewed = Product.query.filter(
                Product.slug.in_(recent_slugs), Product.status == 'active'
            ).all()
            # Preserve order as in recent_slugs
            slug_to_prod = {p.slug: p for p in recently_viewed}
            recently_viewed = [slug_to_prod[s] for s in recent_slugs if s in slug_to_prod]
        else:
            recently_viewed = []
    except Exception:
        recently_viewed = []

    return render_template('peptides/detail.html', product=product, related_products=related_products, recently_viewed=recently_viewed)

# ----------------------
# Favorites (Wishlist)
# ----------------------

@app.route('/favorites')
@login_required
def favorites():
    # List the current user's favorite products
    favs = FavoriteProduct.query.filter_by(user_id=current_user.id).order_by(FavoriteProduct.created_at.desc()).all()
    product_ids = [f.product_id for f in favs]
    products = []
    if product_ids:
        products = Product.query.filter(Product.id.in_(product_ids), Product.status == 'active').all()
        # Preserve order based on favs order
        by_id = {p.id: p for p in products}
        products = [by_id[i] for i in product_ids if i in by_id]
    return render_template('favorites/index.html', products=products)

@app.route('/favorites/toggle', methods=['POST'])
@login_required
def toggle_favorite():
    product_id = request.form.get('product_id', type=int)
    if not product_id:
        return jsonify({'success': False, 'error': 'Missing product_id'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    fav = FavoriteProduct.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    favorited = False
    if fav:
        db.session.delete(fav)
        db.session.commit()
        favorited = False
        flash('Removed from wishlist', 'success')
    else:
        new_fav = FavoriteProduct(user_id=current_user.id, product_id=product_id)
        db.session.add(new_fav)
        db.session.commit()
        favorited = True
        flash('Added to wishlist', 'success')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'favorited': favorited})
    return redirect(request.referrer or url_for('favorites'))

@app.route('/stock-alerts', methods=['POST'])
def create_stock_alert():
    product_id = request.form.get('product_id', type=int)
    email = request.form.get('email', type=str)
    if not product_id:
        return jsonify({'success': False, 'error': 'Missing product_id'}), 400
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    # Determine contact
    user_id = None
    contact_email = None
    if current_user and getattr(current_user, 'is_authenticated', False):
        user_id = current_user.id
        contact_email = current_user.email
    elif email:
        contact_email = email.strip()

    if not user_id and not contact_email:
        # Must provide an email when not logged in
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Email required'}), 400
        flash('Please provide a valid email for notifications.', 'error')
        return redirect(request.referrer or url_for('peptide_detail', slug=product.slug))

    # Upsert-like behavior: look for existing active alert
    q = StockAlert.query.filter_by(product_id=product_id, active=True)
    if user_id:
        q = q.filter_by(user_id=user_id)
    else:
        q = q.filter_by(email=contact_email)
    existing = q.first()
    if existing:
        # Already subscribed
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'already_subscribed': True})
        flash('You will be notified when this item is back in stock.', 'success')
        return redirect(request.referrer or url_for('peptide_detail', slug=product.slug))

    alert = StockAlert(product_id=product_id, user_id=user_id, email=contact_email, active=True)
    db.session.add(alert)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    flash('We will notify you when this item is back in stock.', 'success')
    return redirect(request.referrer or url_for('peptide_detail', slug=product.slug))

# Shopping Cart Routes
@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(
        ((item.product.sale_price if item.product.sale_price is not None else item.product.price) * item.quantity)
        for item in cart_items
    )
    # Free shipping progress
    try:
        free_shipping_threshold = float(os.getenv('FREE_SHIPPING_THRESHOLD', '99'))
    except Exception:
        free_shipping_threshold = 99.0
    shipping_remaining = float(max(0.0, free_shipping_threshold - float(total)))
    shipping_progress = int(100 if free_shipping_threshold <= 0 else min(100.0, (float(total) / free_shipping_threshold) * 100.0))

    return render_template('cart/index.html', cart_items=cart_items, total=total,
                           free_shipping_threshold=free_shipping_threshold,
                           shipping_remaining=shipping_remaining,
                           shipping_progress=shipping_progress)

@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    product = Product.query.get_or_404(product_id)

    if not product.is_in_stock():
        flash('Product is out of stock', 'error')
        return redirect(url_for('peptide_detail', slug=product.slug))

    # Check if item already in cart
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    # Enforce stock limits
    if cart_item:
        new_qty = cart_item.quantity + quantity
        if new_qty > product.stock_quantity:
            flash(f'Only {product.stock_quantity} units available in stock.', 'error')
            return redirect(url_for('peptide_detail', slug=product.slug))
        cart_item.quantity = new_qty
    else:
        if quantity > product.stock_quantity:
            flash(f'Only {product.stock_quantity} units available in stock.', 'error')
            return redirect(url_for('peptide_detail', slug=product.slug))
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    db.session.commit()

    # Compute updated cart count (sum of quantities)
    cart_count = db.session.query(func.coalesce(db.func.sum(CartItem.quantity), 0)).filter(
        CartItem.user_id == current_user.id
    ).scalar() or 0

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': int(cart_count)})

    flash('Product added to cart', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity', 1))

    cart_item = CartItem.query.get_or_404(item_id)

    if cart_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if quantity > 0:
        # Enforce stock constraints
        if quantity > cart_item.product.stock_quantity:
            return jsonify({'success': False, 'error': 'Insufficient stock', 'available': cart_item.product.stock_quantity}), 400
        cart_item.quantity = quantity
        db.session.commit()
        effective_price = cart_item.product.sale_price if cart_item.product.sale_price is not None else cart_item.product.price
        # Updated cart total
        cart_total = db.session.query(func.coalesce(db.func.sum((func.coalesce(Product.sale_price, Product.price) * CartItem.quantity)), 0)).join(
            Product, Product.id == CartItem.product_id
        ).filter(CartItem.user_id == current_user.id).scalar() or 0
        return jsonify({'success': True, 'item_total': float(effective_price * cart_item.quantity), 'cart_total': float(cart_total)})
    else:
        db.session.delete(cart_item)
        db.session.commit()
        cart_total = db.session.query(func.coalesce(db.func.sum((func.coalesce(Product.sale_price, Product.price) * CartItem.quantity)), 0)).join(
            Product, Product.id == CartItem.product_id
        ).filter(CartItem.user_id == current_user.id).scalar() or 0
        return jsonify({'success': True, 'removed': True, 'cart_total': float(cart_total)})

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    if cart_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

# Orders Routes
@app.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('orders/index.html', orders=orders)

@app.route('/orders/<order_number>')
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template('orders/detail.html', order=order)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))

    total = sum(
        ((item.product.sale_price if item.product.sale_price is not None else item.product.price) * item.quantity)
        for item in cart_items
    )

    if request.method == 'POST':
        # Build structured addresses
        shipping_address = {
            'name': request.form.get('shipping_name'),
            'phone': request.form.get('shipping_phone'),
            'address': request.form.get('shipping_address'),
            'city': request.form.get('shipping_city'),
            'state': request.form.get('shipping_state'),
            'postal_code': request.form.get('shipping_postal'),
            'country': request.form.get('shipping_country'),
        }

        billing_address = {
            'name': request.form.get('billing_name'),
            'phone': request.form.get('billing_phone'),
            'address': request.form.get('billing_address'),
            'city': request.form.get('billing_city'),
            'state': request.form.get('billing_state'),
            'postal_code': request.form.get('billing_postal'),
            'country': request.form.get('billing_country'),
        }

        # If billing not provided, default to shipping
        if not billing_address.get('name') and not billing_address.get('address'):
            billing_address = shipping_address

        # Preflight stock check
        shortages = []
        for cart_item in cart_items:
            if cart_item.product.stock_quantity < cart_item.quantity:
                shortages.append((cart_item.product.name, cart_item.product.stock_quantity, cart_item.quantity))

        if shortages:
            for name, available, needed in shortages:
                flash(f'Insufficient stock for {name}. Available: {available}, In cart: {needed}', 'error')
            return redirect(url_for('cart'))

        # Create order and update stock within a transaction with row locks
        try:
            with db.session.begin():
                order_number = generate_order_number()
                order = Order(
                    order_number=order_number,
                    user_id=current_user.id,
                    total_amount=total,
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    notes=request.form.get('notes')
                )
                db.session.add(order)
                db.session.flush()

                for cart_item in cart_items:
                    # Lock the product row for update
                    product = Product.query.filter_by(id=cart_item.product_id).with_for_update().one()
                    effective_price = cart_item.product.sale_price if cart_item.product.sale_price is not None else cart_item.product.price

                    if product.stock_quantity < cart_item.quantity:
                        raise ValueError(f"Insufficient stock for {product.name}")

                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=cart_item.product_id,
                        quantity=cart_item.quantity,
                        price=effective_price,
                        total=effective_price * cart_item.quantity
                    )
                    db.session.add(order_item)

                    # Decrement stock safely
                    product.stock_quantity = product.stock_quantity - cart_item.quantity

                # Clear cart for user
                CartItem.query.filter_by(user_id=current_user.id).delete()

            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_detail', order_number=order_number))
        except Exception as e:
            db.session.rollback()
            flash(f'Checkout failed: {str(e)}', 'error')
            return redirect(url_for('cart'))

    return render_template('checkout/index.html', cart_items=cart_items, total=total)

# Payments Routes
@app.route('/payments')
@login_required
def payments():
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.join(Order).filter(Order.user_id == current_user.id).order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('payments/index.html', payments=payments)

@app.route('/payments/<int:payment_id>')
@login_required
def payment_detail(payment_id):
    payment = Payment.query.join(Order).filter(
        Payment.id == payment_id,
        Order.user_id == current_user.id
    ).first_or_404()
    return render_template('payments/detail.html', payment=payment)

# Peptide Calculator Route
@app.route('/calculator')
def calculator():
    return render_template('calculator/index.html')

# Static Pages Routes
@app.route('/privacy')
def privacy():
    return render_template('static/privacy.html')

@app.route('/terms')
def terms():
    return render_template('static/terms.html')

@app.route('/shipping')
def shipping():
    return render_template('static/shipping.html')

# Tracker Routes
@app.route('/tracker')
@login_required
def tracker():
    # Get user's active cycles
    active_cycles = PeptideCycle.query.filter_by(user_id=current_user.id, status='active').all()

    # Calculate stats
    active_cycles_count = len(active_cycles)

    # Get total injections
    total_injections = DosageLog.query.join(PeptideCycle).filter(
        PeptideCycle.user_id == current_user.id
    ).count()

    # Calculate weight change (compare first and last progress entry)
    progress_entries = ProgressEntry.query.join(PeptideCycle).filter(
        PeptideCycle.user_id == current_user.id
    ).order_by(ProgressEntry.entry_date).all()

    weight_change = 0
    if len(progress_entries) >= 2:
        first_weight = progress_entries[0].weight
        last_weight = progress_entries[-1].weight
        if first_weight and last_weight:
            weight_change = last_weight - first_weight

    # Calculate days tracked
    days_tracked = 0
    if progress_entries:
        first_date = progress_entries[0].entry_date
        last_date = progress_entries[-1].entry_date
        days_tracked = (last_date - first_date).days + 1

    # Get recent activity
    recent_dosages = DosageLog.query.join(PeptideCycle).filter(
        PeptideCycle.user_id == current_user.id
    ).order_by(DosageLog.injection_time.desc()).limit(5).all()

    recent_progress = ProgressEntry.query.join(PeptideCycle).filter(
        PeptideCycle.user_id == current_user.id
    ).order_by(ProgressEntry.entry_date.desc()).limit(5).all()

    # Get products for new cycle creation
    products = Product.query.filter_by(status='active').all()

    return render_template('tracker/index.html',
                         active_cycles=active_cycles,
                         active_cycles_count=active_cycles_count,
                         total_injections=total_injections,
                         weight_change=weight_change,
                         days_tracked=days_tracked,
                         recent_dosages=recent_dosages,
                         recent_progress=recent_progress,
                         products=products)

@app.route('/tracker/create-cycle', methods=['POST'])
@login_required
def create_cycle():
    name = request.form.get('name')
    product_id = request.form.get('product_id')
    start_date = request.form.get('start_date')
    target_dosage = request.form.get('target_dosage')
    frequency = request.form.get('frequency')
    notes = request.form.get('notes')

    cycle = PeptideCycle(
        user_id=current_user.id,
        name=name,
        product_id=int(product_id) if product_id else None,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
        target_dosage=float(target_dosage) if target_dosage else None,
        frequency=frequency,
        notes=notes
    )

    db.session.add(cycle)
    db.session.commit()

    flash('Cycle created successfully!', 'success')
    return redirect(url_for('tracker'))

@app.route('/tracker/log-dosage', methods=['GET', 'POST'])
@login_required
def log_dosage():
    if request.method == 'POST':
        cycle_id = request.form.get('cycle_id')
        dosage_amount = request.form.get('dosage_amount')
        injection_time = request.form.get('injection_time')
        injection_site = request.form.get('injection_site')
        notes = request.form.get('notes')

        dosage = DosageLog(
            cycle_id=int(cycle_id),
            dosage_amount=float(dosage_amount),
            injection_time=datetime.strptime(injection_time, '%Y-%m-%dT%H:%M'),
            injection_site=injection_site,
            notes=notes
        )

        db.session.add(dosage)
        db.session.commit()

        flash('Dosage logged successfully!', 'success')
        return redirect(url_for('tracker'))

    # GET request - show form
    active_cycles = PeptideCycle.query.filter_by(user_id=current_user.id, status='active').all()
    selected_cycle_id = request.args.get('cycle_id', type=int)

    return render_template('tracker/log_dosage.html',
                         active_cycles=active_cycles,
                         selected_cycle_id=selected_cycle_id)

@app.route('/tracker/add-progress', methods=['GET', 'POST'])
@login_required
def add_progress():
    if request.method == 'POST':
        cycle_id = request.form.get('cycle_id')
        entry_date = request.form.get('entry_date')
        weight = request.form.get('weight')
        body_fat_percentage = request.form.get('body_fat_percentage')
        muscle_mass = request.form.get('muscle_mass')
        energy_level = request.form.get('energy_level')
        mood = request.form.get('mood')
        side_effects = request.form.get('side_effects')
        notes = request.form.get('notes')

        progress = ProgressEntry(
            cycle_id=int(cycle_id),
            entry_date=datetime.strptime(entry_date, '%Y-%m-%d').date(),
            weight=float(weight) if weight else None,
            body_fat_percentage=float(body_fat_percentage) if body_fat_percentage else None,
            muscle_mass=float(muscle_mass) if muscle_mass else None,
            energy_level=int(energy_level) if energy_level else None,
            mood=mood,
            side_effects=side_effects,
            notes=notes
        )

        db.session.add(progress)
        db.session.commit()

        flash('Progress entry added successfully!', 'success')
        return redirect(url_for('tracker'))

    # GET request - show form
    active_cycles = PeptideCycle.query.filter_by(user_id=current_user.id, status='active').all()

    return render_template('tracker/add_progress.html', active_cycles=active_cycles)

# Error Handlers
@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)
