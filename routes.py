from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Post, Product, Category, CartItem, Order, OrderItem, Payment, User
from werkzeug.utils import secure_filename
import uuid
import os
from datetime import datetime

bp = Blueprint('main', __name__)

# Helper functions
def generate_slug(title):
    """Generate URL-friendly slug from title"""
    return title.lower().replace(' ', '-').replace('_', '-')

def generate_order_number():
    """Generate unique order number"""
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

# Blog Posts Routes
@bp.route('/posts')
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(status='published').order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('posts/index.html', posts=posts)

@bp.route('/posts/<slug>')
def post_detail(slug):
    post = Post.query.filter_by(slug=slug, status='published').first_or_404()
    return render_template('posts/detail.html', post=post)

# Products Routes
@bp.route('/peptides')
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

@bp.route('/peptides/<slug>')
def peptide_detail(slug):
    product = Product.query.filter_by(slug=slug, status='active').first_or_404()
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.status == 'active'
    ).limit(4).all()
    return render_template('peptides/detail.html', product=product, related_products=related_products)

# Shopping Cart Routes
@bp.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart/index.html', cart_items=cart_items, total=total)

@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))

    product = Product.query.get_or_404(product_id)

    if not product.is_in_stock():
        flash('Product is out of stock', 'error')
        return redirect(url_for('main.peptide_detail', slug=product.slug))

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
    return redirect(url_for('main.cart'))

@bp.route('/cart/update', methods=['POST'])
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

@bp.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)

    if cart_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart', 'success')
    return redirect(url_for('main.cart'))

# Orders Routes
@bp.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('orders/index.html', orders=orders)

@bp.route('/orders/<order_number>')
@login_required
def order_detail(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    return render_template('orders/detail.html', order=order)

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('main.cart'))

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
        return redirect(url_for('main.order_detail', order_number=order_number))

    return render_template('checkout/index.html', cart_items=cart_items, total=total)

# Payments Routes
@bp.route('/payments')
@login_required
def payments():
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.join(Order).filter(Order.user_id == current_user.id).order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template('payments/index.html', payments=payments)

@bp.route('/payments/<int:payment_id>')
@login_required
def payment_detail(payment_id):
    payment = Payment.query.join(Order).filter(
        Payment.id == payment_id,
        Order.user_id == current_user.id
    ).first_or_404()
    return render_template('payments/detail.html', payment=payment)