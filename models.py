from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum
try:
    # Optional: only available when using Postgres with pgvector
    from pgvector.sqlalchemy import Vector  # type: ignore
except Exception:  # pragma: no cover
    Vector = None

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    picture = db.Column(db.String(200))
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NewsletterSubscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(120))
    utm_source = db.Column(db.String(100))
    utm_medium = db.Column(db.String(100))
    utm_campaign = db.Column(db.String(100))
    referrer = db.Column(db.String(500))
    user_agent = db.Column(db.String(500))
    ip_address = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    unsubscribe_token = db.Column(db.String(64), unique=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    confirmed = db.Column(db.Boolean, default=True)  # set to False to require double opt-in in future

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.String(300))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='published')  # draft, published, archived
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)

    author = db.relationship('User', backref='posts')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2))
    sku = db.Column(db.String(100), unique=True, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    featured_image = db.Column(db.String(300))
    images = db.Column(db.JSON)  # Array of image URLs
    status = db.Column(db.String(20), default='active')  # active, inactive, out_of_stock
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('Category', backref='products')

    def is_in_stock(self):
        return self.stock_quantity > 0 and self.status == 'active'

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

class FavoriteProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='favorite_products')
    product = db.relationship('Product', backref='favorited_by')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='uq_favorite_product'),
    )

class StockAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    active = db.Column(db.Boolean, default=True)
    notified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    user = db.relationship('User')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    shipping_address = db.Column(db.JSON)
    billing_address = db.Column(db.JSON)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='orders')
    order_items = db.relationship('OrderItem', backref='order', lazy=True)
    payments = db.relationship('Payment', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # stripe, paypal, bank_transfer
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    payment_data = db.Column(db.JSON)  # Store payment gateway response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Tracker Models
class PeptideCycle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    target_dosage = db.Column(db.Numeric(10, 2), nullable=True)  # mg per dose
    frequency = db.Column(db.String(50), nullable=True)  # daily, weekly, etc.
    status = db.Column(db.String(20), default='active')  # active, completed, paused
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='peptide_cycles')
    product = db.relationship('Product')
    dosage_logs = db.relationship('DosageLog', backref='cycle', lazy=True, cascade='all, delete-orphan')
    progress_entries = db.relationship('ProgressEntry', backref='cycle', lazy=True, cascade='all, delete-orphan')

class DosageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('peptide_cycle.id'), nullable=False)
    dosage_amount = db.Column(db.Numeric(10, 2), nullable=False)  # mg
    injection_time = db.Column(db.DateTime, nullable=False)
    injection_site = db.Column(db.String(100), nullable=True)  # stomach, thigh, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProgressEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey('peptide_cycle.id'), nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Numeric(6, 2), nullable=True)  # kg
    body_fat_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    muscle_mass = db.Column(db.Numeric(6, 2), nullable=True)
    notes = db.Column(db.Text)
    energy_level = db.Column(db.Integer, nullable=True)  # 1-10 scale
    mood = db.Column(db.String(50), nullable=True)  # excellent, good, average, poor
    side_effects = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Community Models

# Association table for many-to-many relation between community posts and tags
community_post_tags = db.Table(
    'community_post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('community_post.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('community_tag.id'), primary_key=True)
)

class CommunityPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='published')  # draft, published, archived
    view_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)  # upvotes - downvotes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='community_posts')
    tags = db.relationship('CommunityTag', secondary=community_post_tags, backref='posts')

class CommunityComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post = db.relationship('CommunityPost', backref='comments')
    user = db.relationship('User')

class CommunityVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('community_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)  # -1 or +1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post = db.relationship('CommunityPost', backref='votes')
    user = db.relationship('User')

    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='uq_community_vote'),
    )

class CommunityTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SearchDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False)  # 'product' or 'post'
    ref_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    # Dimension defaults to 1536 for text-embedding-3-small; ignored if Vector not available
    if Vector is not None:
        embedding = db.Column(Vector(1536))  # type: ignore
    else:
        # Fallback placeholder when not using Postgres; column won't be used
        embedding = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('kind', 'ref_id', name='uq_search_document_kind_ref'),
    )