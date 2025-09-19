from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from auth import google_auth, login_manager, create_or_update_user
from models import db, Post, Product, Category, CartItem, Order, OrderItem, Payment, User, PeptideCycle, DosageLog, ProgressEntry
from dotenv import load_dotenv
import re
import os
import secrets
import uuid
import pymysql
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask app
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://mariadb:0cZ0FRFBB1UPsmnTKjGfm8iofaBkb0s7JZAggtz1f3RGnqqnu7d2h6dk6zF8EGbv@104.248.150.75:33004/default')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
from models import db
db.init_app(app)

# Register template filters
from template_filters import markdown_filter, excerpt_filter, reading_time_filter, truncate_filter
app.jinja_env.filters['markdown'] = markdown_filter
app.jinja_env.filters['excerpt'] = excerpt_filter
app.jinja_env.filters['reading_time'] = reading_time_filter
app.jinja_env.filters['truncate'] = truncate_filter

login_manager.init_app(app)


# Helper functions
def generate_slug(title):
    """Generate URL-friendly slug from title"""
    return title.lower().replace(' ', '-').replace('_', '-')

def generate_order_number():
    """Generate unique order number"""
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    auth_url = google_auth.get_auth_url()
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
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_info = 'asd'
    return render_template('dashboard.html', user=user_info)

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

    return render_template(
        'posts/detail.html',
        post=post,
        related_posts=related_posts,
        prev_post=prev_post,
        next_post=next_post
    )

def get_related_posts(current_post, limit=3):
    """Get related posts based on content similarity"""
    # Extract keywords from current post
    current_keywords = extract_keywords(current_post.title + ' ' + current_post.excerpt)

    # Get all published posts except current post
    all_posts = Post.query.filter(
        Post.status == 'published',
        Post.id != current_post.id
    ).all()

    # Score each post based on keyword matches
    scored_posts = []
    for post in all_posts:
        post_keywords = extract_keywords(post.title + ' ' + post.excerpt)
        score = calculate_similarity(current_keywords, post_keywords)

        # Boost score for posts with similar content themes
        if has_similar_theme(current_post.content, post.content):
            score += 2

        if score > 0:
            scored_posts.append((post, score))

    # Sort by score and return top posts
    scored_posts.sort(key=lambda x: x[1], reverse=True)
    return [post for post, score in scored_posts[:limit]]

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

# Products Routes
@app.route('/peptides')
def peptides():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)

    query = Product.query.filter_by(status='active')
    if category_id:
        query = query.filter_by(category_id=category_id)

    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    categories = Category.query.all()

    return render_template('peptides/index.html', products=products, categories=categories, selected_category=category_id)

@app.route('/peptides/<slug>')
def peptide_detail(slug):
    product = Product.query.filter_by(slug=slug, status='active').first_or_404()
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.status == 'active'
    ).limit(4).all()
    return render_template('peptides/detail.html', product=product, related_products=related_products)

# Shopping Cart Routes
@app.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart/index.html', cart_items=cart_items, total=total)

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

    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    db.session.commit()
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
        cart_item.quantity = quantity
        db.session.commit()
        return jsonify({'success': True, 'total': cart_item.product.price * cart_item.quantity})
    else:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'success': True, 'removed': True})

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

    total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        # Create order
        order_number = generate_order_number()
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            total_amount=total,
            shipping_address=request.form.get('shipping_address'),
            billing_address=request.form.get('billing_address'),
            notes=request.form.get('notes')
        )
        db.session.add(order)
        db.session.flush()  # Get order ID

        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                total=cart_item.product.price * cart_item.quantity
            )
            db.session.add(order_item)

            # Update product stock
            cart_item.product.stock_quantity -= cart_item.quantity

        # Clear cart
        CartItem.query.filter_by(user_id=current_user.id).delete()

        db.session.commit()

        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_detail', order_number=order_number))

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
